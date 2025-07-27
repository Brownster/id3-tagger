import tempfile
from pathlib import Path
from mp3_id3_processor.api_server import parse_m3u


def test_parse_m3u_absolute_paths(tmp_path: Path):
    m3u = tmp_path / "playlist.m3u"
    lines = [
        "#EXTM3U",
    ]
    files = []
    for i in range(3):
        f = tmp_path / f"file{i}.mp3"
        f.write_text("dummy")
        lines.append(str(f))
        files.append(f.resolve())
    m3u.write_text("\n".join(lines))

    parsed = parse_m3u(m3u)
    assert parsed == files


def test_parse_m3u_relative_paths(tmp_path: Path):
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    m3u = tmp_path / "playlist.m3u"
    files = []
    lines = ["#EXTM3U"]
    for i in range(2):
        f = music_dir / f"song{i}.mp3"
        f.write_text("dummy")
        lines.append(f"song{i}.mp3")
        files.append(f.resolve())
    m3u.write_text("\n".join(lines))

    parsed = parse_m3u(m3u, music_dir)
    assert parsed == files
