from __future__ import annotations

"""Simple Flask API server for MP3 ID3 processing."""

from pathlib import Path
from typing import List, Optional

from flask import Flask, jsonify, request

from .config import Configuration
from .scanner import FileScanner
from .processor import ID3Processor
from .metadata_extractor import MetadataExtractor
from .musicbrainz_client import MusicBrainzClient
from .logger import ProcessingLogger
from .models import ProcessingResults, ProcessingResult

app = Flask(__name__)


def parse_m3u(m3u_path: Path, music_directory: Optional[Path] = None) -> List[Path]:
    """Parse an M3U playlist and return a list of file paths."""
    paths: List[Path] = []
    base_dir = music_directory if music_directory else m3u_path.parent
    with open(m3u_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = Path(line)
            if not p.is_absolute():
                p = base_dir / line
            paths.append(p.resolve())
    return paths


def _generate_report_text(results: ProcessingResults) -> str:
    lines = [
        "PROCESSING SUMMARY",
        "===================",
        f"Total files found: {results.total_files}",
        f"Files processed: {results.processed_files}",
        f"Files modified: {results.files_modified}",
    ]
    if results.tags_added_count:
        lines.append("Tags added:")
        for tag, count in results.tags_added_count.items():
            lines.append(f"  {tag}: {count}")
    if results.errors:
        lines.append("Errors:")
        for res in results.errors:
            lines.append(f"  {res.file_path}: {res.error_message}")
    return "\n".join(lines)


def _process_files(paths: List[Path], config: Configuration) -> ProcessingResults:
    logger = ProcessingLogger(verbose=config.verbose)
    processor = ID3Processor(config)
    extractor = MetadataExtractor()
    mb_client = MusicBrainzClient() if config.use_api else None

    results = ProcessingResults(total_files=len(paths))
    logger.log_start(len(paths))

    # Remove album caching to ensure accurate metadata for various artist albums
    # Each track will get its own API lookup for proper genre/year detection

    for p in paths:
        meta = extractor.extract_metadata(p)
        if not meta:
            result = ProcessingResult(p, False, [], "Could not extract metadata")
            results.add_result(result)
            logger.log_error(p, Exception(result.error_message))
            continue

        genre = meta.genre
        year = meta.year

        # Get metadata from API if enabled and track needs tags
        if config.use_api and mb_client and meta.has_lookup_info():
            if (not genre and meta.needs_genre()) or (not year and meta.needs_year()):
                mb = mb_client.get_metadata(meta.artist or "", meta.album or "", meta.title or "")
                if mb:
                    if not genre and mb.genre:
                        genre = mb.genre
                    if not year and mb.year:
                        year = mb.year

        # Only use values obtained from API - no default fallbacks

        result = processor.process_file(p, genre=genre, year=year)
        results.add_result(result)
        if result.success:
            logger.log_file_processing(p, result.tags_added)
        else:
            logger.log_error(p, Exception(result.error_message or "Processing failed"))

    logger.log_summary(results)
    return results


@app.route("/process_directory", methods=["POST"])
def process_directory_endpoint():
    data = request.get_json(silent=True) or {}
    directory = data.get("directory")
    if not directory:
        return jsonify({"error": "directory required"}), 400
    dir_path = Path(directory)
    scanner = FileScanner()
    try:
        mp3_files = scanner.scan_directory(dir_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    results = _process_files(mp3_files, app.config["CONFIG"])
    report_path = Path("api_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(_generate_report_text(results))
    return jsonify({"processed": results.processed_files, "report": str(report_path)})


@app.route("/process_playlist", methods=["POST"])
def process_playlist_endpoint():
    data = request.get_json(silent=True) or {}
    m3u = data.get("m3u_path")
    if not m3u:
        return jsonify({"error": "m3u_path required"}), 400
    music_dir = data.get("music_directory")
    try:
        paths = parse_m3u(Path(m3u), Path(music_dir) if music_dir else None)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    results = _process_files(paths, app.config["CONFIG"])
    report_path = Path("api_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(_generate_report_text(results))
    return jsonify({"processed": results.processed_files, "report": str(report_path)})


def run_api_server(config: Configuration, host: str = "0.0.0.0", port: int = 5000):
    """Run the Flask API server."""
    app.config["CONFIG"] = config
    app.run(host=host, port=port)
