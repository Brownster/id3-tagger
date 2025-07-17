import pytest
from pathlib import Path

@pytest.fixture
def music_dir(tmp_path: Path) -> Path:
    dir_path = tmp_path / "music"
    dir_path.mkdir()
    return dir_path
