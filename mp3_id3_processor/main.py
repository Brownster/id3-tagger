"""Main entry point for the MP3 ID3 processor application."""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Tuple

from .config import Configuration
from .scanner import FileScanner, ScannerError, DirectoryAccessError
from .processor import ID3Processor
from .logger import ProcessingLogger
from .models import ProcessingResults, ProcessingResult
from .metadata_extractor import MetadataExtractor
from .musicbrainz_client import MusicBrainzClient


def parse_arguments() -> argparse.Namespace:
    """Parse and validate command-line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Automatically add missing genre ID3 tags to MP3 files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Process ~/Music with API lookups enabled
  %(prog)s --verbose                # Show detailed progress information
  %(prog)s --no-api                 # Disable API lookups (only use existing metadata)
  %(prog)s --config config.json     # Use custom configuration file
  %(prog)s --directory /path/to/music    # Process custom directory
  %(prog)s --cache-dir ./cache      # Use custom cache directory for API responses
        """
    )
    
    parser.add_argument(
        '--directory', '-d',
        type=str,
        help='Directory to scan for MP3 files (default: ~/Music)'
    )
    
    parser.add_argument(
        '--no-api',
        action='store_true',
        help='Disable API lookups and only process files with existing metadata'
    )
    
    parser.add_argument(
        '--api-timeout',
        type=float,
        default=10.0,
        help='API request timeout in seconds (default: 10.0)'
    )
    
    parser.add_argument(
        '--cache-dir',
        type=str,
        help='Directory for API response cache'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file (JSON format)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output showing detailed progress'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making any changes'
    )

    parser.add_argument(
        '--report-missing',
        action='store_true',
        help='With --dry-run, scan and report files missing genre or year'
    )

    parser.add_argument(
        '--genre',
        type=str,
        help='Override default genre to add to files'
    )

    parser.add_argument(
        '--api-mode',
        action='store_true',
        help='Start a simple HTTP API server instead of processing once'
    )

    
    return parser.parse_args()


def display_summary(results: ProcessingResults):
    """Display final processing summary.
    
    Args:
        results: ProcessingResults containing processing statistics.
    """
    # The logger already handles summary display, but we can add
    # additional summary information here if needed
    pass


def validate_music_directory(directory: Path) -> bool:
    """Validate that the music directory exists and is accessible.
    
    Args:
        directory: Path to the music directory.
        
    Returns:
        True if directory is valid, False otherwise.
    """
    try:
        if not directory.exists():
            print(f"Error: Music directory does not exist: {directory}")
            print("Please ensure the directory exists or specify a different directory with --directory")
            return False
        
        if not directory.is_dir():
            print(f"Error: Path is not a directory: {directory}")
            return False
        
        # Test if we can read the directory
        try:
            list(directory.iterdir())
        except PermissionError:
            print(f"Error: Permission denied accessing directory: {directory}")
            print("Please check directory permissions")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error: Cannot access directory {directory}: {e}")
        return False


def main():
    """Main entry point for the MP3 ID3 processor"""
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Initialize configuration
        config_file = Path(args.config) if args.config else None
        config = Configuration(config_file)
        
        # Override configuration with command-line arguments
        config_updates = {}
        if args.directory:
            config_updates['music_directory'] = args.directory
        if args.no_api:
            config_updates['use_api'] = False
        if args.api_timeout:
            config_updates['api_timeout'] = args.api_timeout
        if args.cache_dir:
            config_updates['api_cache_dir'] = args.cache_dir
        if args.verbose:
            config_updates['verbose'] = True
        if args.genre:
            config_updates['default_genre'] = args.genre
        
        if config_updates:
            if not config.update_from_dict(config_updates):
                print("Error: Invalid configuration values provided")
                sys.exit(1)
        
        if args.api_mode:
            from .api_server import run_api_server
            run_api_server(config)
            sys.exit(0)

        # Validate music directory
        music_dir = config.music_directory
        if not validate_music_directory(music_dir):
            sys.exit(1)
        
        # Initialize components
        logger = ProcessingLogger(verbose=config.verbose)
        scanner = FileScanner()
        processor = ID3Processor(config, dry_run=args.dry_run)
        
        # Initialize API components if enabled
        metadata_extractor = MetadataExtractor()
        musicbrainz_client = None
        if config.use_api:
            musicbrainz_client = MusicBrainzClient()
        
        # Display startup information
        if config.verbose:
            print(f"Configuration:")
            print(f"  Music directory: {music_dir}")
            print(f"  API lookups: {'enabled' if config.use_api else 'disabled'}")
            print(f"  Verbose mode: {config.verbose}")
            if args.dry_run:
                print(f"  Dry run mode: enabled")
            print()
        
        # Scan for MP3 files
        try:
            mp3_files = scanner.scan_directory(music_dir)
        except DirectoryAccessError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except ScannerError as e:
            print(f"Error scanning directory: {e}")
            sys.exit(1)

        # Check if any MP3 files were found
        if not mp3_files:
            print(f"No MP3 files found in {music_dir}")
            print("Please check that the directory contains MP3 files")
            sys.exit(0)

        if args.dry_run and args.report_missing:
            extractor = MetadataExtractor()
            missing = {}
            for fp in mp3_files:
                meta = extractor.extract_metadata(fp)
                if not meta:
                    continue
                missing_tags = []
                if meta.needs_genre():
                    missing_tags.append('genre')
                if meta.needs_year():
                    missing_tags.append('year')
                if missing_tags:
                    missing[fp] = missing_tags
            if missing:
                print("FILES MISSING TAGS:")
                for p, tags in missing.items():
                    print(f"  {p.name}: missing {', '.join(tags)}")
            else:
                print("All files have genre and year tags")
            sys.exit(0)
        
        # Initialize processing results
        results = ProcessingResults(total_files=len(mp3_files))
        
        # Start processing
        logger.log_start(len(mp3_files))

        # Cache API results per album directory to minimize API calls
        album_cache: Dict[str, Tuple[Optional[str], Optional[str]]] = {}
        
        if args.dry_run:
            print("DRY RUN MODE - No files will be modified")
            print("-" * 50)
        
        # Process each file with progress reporting
        for i, file_path in enumerate(mp3_files, 1):
            try:
                # Report progress for large collections
                if len(mp3_files) > 10 and config.verbose:
                    logger.log_progress_update(i, len(mp3_files), file_path.name)

                # Allow processor to handle file directly if genre/year are provided
                direct_result = processor.process_file(file_path)
                if isinstance(direct_result, ProcessingResult):
                    results.add_result(direct_result)
                    if direct_result.success:
                        logger.log_file_processing(file_path, direct_result.tags_added)
                    else:
                        logger.log_error(file_path, Exception(direct_result.error_message or "Processing failed"))
                    continue

                # Extract existing metadata
                existing_metadata = metadata_extractor.extract_metadata(file_path)
                if not existing_metadata:
                    # Skip files we can't read
                    error_result = ProcessingResult(
                        file_path=file_path,
                        success=False,
                        error_message="Could not extract metadata from file"
                    )
                    results.add_result(error_result)
                    logger.log_error(file_path, Exception("Could not extract metadata"))
                    continue
                
                # Skip files that already have a genre tag
                if not existing_metadata.needs_genre():
                    if config.verbose:
                        print(f"[{i}/{len(mp3_files)}] {file_path.name}: Already has genre")
                    result = ProcessingResult(file_path=file_path, success=True, tags_added=[])
                    results.add_result(result)
                    missing = []
                    if existing_metadata.needs_genre() and 'genre' not in result.tags_added:
                        missing.append('genre')
                    if existing_metadata.needs_year() and 'year' not in result.tags_added:
                        missing.append('year')
                    results.add_missing(file_path, missing)
                    continue
                
                # Try to get metadata from API if enabled
                api_genre = None
                api_year = None

                album_key = str(file_path.parent)
                cached = album_cache.get(album_key)
                if cached is not None:
                    api_genre, api_year = cached
                elif (
                    config.use_api
                    and musicbrainz_client
                    and existing_metadata.has_lookup_info()
                    and existing_metadata.artist
                    and existing_metadata.album
                    and existing_metadata.title
                ):
                    try:
                        mb_metadata = musicbrainz_client.get_metadata(
                            existing_metadata.artist,
                            existing_metadata.album,
                            existing_metadata.title,
                        )
                        if mb_metadata:
                            if mb_metadata.has_genre():
                                api_genre = mb_metadata.genre
                            if mb_metadata.has_year():
                                api_year = mb_metadata.year
                    except Exception as e:
                        logger.log_warning(
                            f"MusicBrainz lookup failed for {file_path.name}: {e}"
                        )
                    album_cache[album_key] = (api_genre, api_year)
                if album_key not in album_cache:
                    album_cache[album_key] = (api_genre, api_year)

                
                # Determine what tags we can add
                tags_to_add = []
                if api_genre and existing_metadata.needs_genre():
                    tags_to_add.append('genre')
                if api_year and existing_metadata.needs_year():
                    tags_to_add.append('year')
                
                if args.dry_run:
                    # In dry run mode, just show what would be done
                    if tags_to_add:
                        tags_str = ", ".join(tags_to_add)
                        details = []
                        if api_genre:
                            details.append(f"genre: {api_genre}")
                        if api_year:
                            details.append(f"year: {api_year}")
                        detail_str = f" ({'; '.join(details)})" if details else ""
                        print(f"Would add {tags_str} to: {file_path.name}{detail_str}")
                        
                        # Create mock result for statistics
                        result = ProcessingResult(file_path=file_path, success=True, tags_added=tags_to_add)
                        results.add_result(result)
                        missing = []
                        if existing_metadata.needs_genre() and 'genre' not in result.tags_added:
                            missing.append('genre')
                        if existing_metadata.needs_year() and 'year' not in result.tags_added:
                            missing.append('year')
                        results.add_missing(file_path, missing)
                    elif config.verbose:
                        if not existing_metadata.has_lookup_info():
                            print(f"No changes for: {file_path.name} (insufficient metadata for lookup)")
                        else:
                            print(f"No changes for: {file_path.name} (no API data found)")
                        result = ProcessingResult(file_path=file_path, success=True, tags_added=[])
                        results.add_result(result)
                        missing = []
                        if existing_metadata.needs_genre():
                            missing.append('genre')
                        if existing_metadata.needs_year():
                            missing.append('year')
                        results.add_missing(file_path, missing)
                else:
                    # Normal processing mode - actually modify files
                    if tags_to_add:
                        # Load the MP3 file for modification
                        audio_file = processor._load_mp3_file(file_path)
                        if audio_file:
                            added_tags = processor.add_missing_tags(
                                audio_file, file_path, api_genre, api_year
                            )
                            result = ProcessingResult(file_path=file_path, success=True, tags_added=added_tags)
                            results.add_result(result)
                            missing = []
                            if existing_metadata.needs_genre() and 'genre' not in result.tags_added:
                                missing.append('genre')
                            if existing_metadata.needs_year() and 'year' not in result.tags_added:
                                missing.append('year')
                            results.add_missing(file_path, missing)
                            logger.log_file_processing(file_path, added_tags)
                        else:
                            error_result = ProcessingResult(
                                file_path=file_path,
                                success=False,
                                error_message="Could not load MP3 file for modification"
                            )
                            results.add_result(error_result)
                            miss = []
                            if existing_metadata.needs_genre():
                                miss.append('genre')
                            if existing_metadata.needs_year():
                                miss.append('year')
                            results.add_missing(file_path, miss)
                            logger.log_error(file_path, Exception("Could not load MP3 file"))
                    else:
                        # No tags to add
                        result = ProcessingResult(file_path=file_path, success=True, tags_added=[])
                        results.add_result(result)
                        missing = []
                        if existing_metadata.needs_genre():
                            missing.append('genre')
                        if existing_metadata.needs_year():
                            missing.append('year')
                        results.add_missing(file_path, missing)
                        if config.verbose:
                            if not existing_metadata.has_lookup_info():
                                logger.log_info(f"{file_path.name}: Insufficient metadata for lookup")
                            else:
                                logger.log_info(f"{file_path.name}: No API data found")
                        
            except KeyboardInterrupt:
                print(f"\nProcessing interrupted by user after {i-1}/{len(mp3_files)} files")
                break
            except Exception as e:
                # Create error result for unexpected exceptions
                error_result = ProcessingResult(
                    file_path=file_path,
                    success=False,
                    error_message=str(e)
                )
                results.add_result(error_result)
                logger.log_error(file_path, e)
                # Continue processing other files
                continue
        
        # Display final summary
        if not args.dry_run:
            logger.log_summary(results)
        else:
            print("\n" + "=" * 50)
            print("DRY RUN SUMMARY")
            print("=" * 50)
            print(f"Total files found: {results.total_files}")
            print(f"Files that would be modified: {results.files_modified}")
            if results.tags_added_count:
                print(f"Tags that would be added:")
                for tag, count in results.tags_added_count.items():
                    print(f"  {tag}: {count} files")
            print("=" * 50)
        
        # Set exit code based on results
        if results.error_count > 0:
            if results.error_count == results.total_files:
                # All files failed
                sys.exit(1)
            else:
                # Some files failed, but some succeeded
                sys.exit(2)
        else:
            # All files processed successfully
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose if 'args' in locals() else False:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()