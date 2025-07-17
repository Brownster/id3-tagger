"""Unit tests for data models."""

import pytest
from pathlib import Path
from datetime import datetime
from mp3_id3_processor.models import ProcessingResult, ProcessingResults, ConfigurationSchema


class TestProcessingResult:
    """Test cases for ProcessingResult dataclass."""

    def test_processing_result_creation_success(self):
        """Test successful creation of ProcessingResult."""
        file_path = Path("/test/file.mp3")
        result = ProcessingResult(
            file_path=file_path,
            success=True,
            tags_added=["genre", "year"],
            error_message=None
        )
        
        assert result.file_path == file_path
        assert result.success is True
        assert result.tags_added == ["genre", "year"]
        assert result.error_message is None

    def test_processing_result_creation_failure(self):
        """Test creation of ProcessingResult for failed processing."""
        file_path = Path("/test/file.mp3")
        result = ProcessingResult(
            file_path=file_path,
            success=False,
            tags_added=[],
            error_message="File corrupted"
        )
        
        assert result.file_path == file_path
        assert result.success is False
        assert result.tags_added == []
        assert result.error_message == "File corrupted"

    def test_processing_result_path_conversion(self):
        """Test that string paths are converted to Path objects."""
        result = ProcessingResult(
            file_path="/test/file.mp3",
            success=True
        )
        
        assert isinstance(result.file_path, Path)
        assert str(result.file_path) == "/test/file.mp3"

    def test_processing_result_validation_success_type(self):
        """Test validation of success field type."""
        with pytest.raises(ValueError, match="success must be a boolean"):
            ProcessingResult(
                file_path=Path("/test/file.mp3"),
                success="true"  # Invalid type
            )

    def test_processing_result_validation_tags_added_type(self):
        """Test validation of tags_added field type."""
        with pytest.raises(ValueError, match="tags_added must be a list"):
            ProcessingResult(
                file_path=Path("/test/file.mp3"),
                success=True,
                tags_added="genre"  # Invalid type
            )

    def test_processing_result_validation_error_message_type(self):
        """Test validation of error_message field type."""
        with pytest.raises(ValueError, match="error_message must be a string or None"):
            ProcessingResult(
                file_path=Path("/test/file.mp3"),
                success=False,
                error_message=123  # Invalid type
            )

    def test_processing_result_defaults(self):
        """Test default values for optional fields."""
        result = ProcessingResult(
            file_path=Path("/test/file.mp3"),
            success=True
        )
        
        assert result.tags_added == []
        assert result.error_message is None


class TestProcessingResults:
    """Test cases for ProcessingResults dataclass."""

    def test_processing_results_creation(self):
        """Test successful creation of ProcessingResults."""
        results = ProcessingResults(total_files=10)
        
        assert results.total_files == 10
        assert results.processed_files == 0
        assert results.files_modified == 0
        assert results.errors == []
        assert results.tags_added_count == {}

    def test_processing_results_validation_total_files(self):
        """Test validation of total_files field."""
        with pytest.raises(ValueError, match="total_files must be a non-negative integer"):
            ProcessingResults(total_files=-1)
        
        with pytest.raises(ValueError, match="total_files must be a non-negative integer"):
            ProcessingResults(total_files="10")

    def test_processing_results_validation_processed_files(self):
        """Test validation of processed_files field."""
        with pytest.raises(ValueError, match="processed_files must be a non-negative integer"):
            ProcessingResults(total_files=10, processed_files=-1)

    def test_processing_results_validation_files_modified(self):
        """Test validation of files_modified field."""
        with pytest.raises(ValueError, match="files_modified must be a non-negative integer"):
            ProcessingResults(total_files=10, files_modified=-1)

    def test_processing_results_validation_processed_exceeds_total(self):
        """Test validation that processed_files doesn't exceed total_files."""
        with pytest.raises(ValueError, match="processed_files cannot exceed total_files"):
            ProcessingResults(total_files=5, processed_files=10)

    def test_processing_results_validation_modified_exceeds_processed(self):
        """Test validation that files_modified doesn't exceed processed_files."""
        with pytest.raises(ValueError, match="files_modified cannot exceed processed_files"):
            ProcessingResults(total_files=10, processed_files=5, files_modified=8)

    def test_add_result_success(self):
        """Test adding a successful processing result."""
        results = ProcessingResults(total_files=5)
        result = ProcessingResult(
            file_path=Path("/test/file.mp3"),
            success=True,
            tags_added=["genre", "year"]
        )
        
        results.add_result(result)
        
        assert results.processed_files == 1
        assert results.files_modified == 1
        assert results.tags_added_count == {"genre": 1, "year": 1}
        assert len(results.errors) == 0

    def test_add_result_success_no_tags(self):
        """Test adding a successful result with no tags added."""
        results = ProcessingResults(total_files=5)
        result = ProcessingResult(
            file_path=Path("/test/file.mp3"),
            success=True,
            tags_added=[]
        )
        
        results.add_result(result)
        
        assert results.processed_files == 1
        assert results.files_modified == 0
        assert results.tags_added_count == {}
        assert len(results.errors) == 0

    def test_add_result_failure(self):
        """Test adding a failed processing result."""
        results = ProcessingResults(total_files=5)
        result = ProcessingResult(
            file_path=Path("/test/file.mp3"),
            success=False,
            error_message="File corrupted"
        )
        
        results.add_result(result)
        
        assert results.processed_files == 1
        assert results.files_modified == 0
        assert results.tags_added_count == {}
        assert len(results.errors) == 1
        assert results.errors[0] == result

    def test_add_result_invalid_type(self):
        """Test adding invalid result type."""
        results = ProcessingResults(total_files=5)
        
        with pytest.raises(ValueError, match="result must be a ProcessingResult instance"):
            results.add_result("invalid")

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        results = ProcessingResults(total_files=10)
        
        # Add successful results
        for i in range(7):
            results.add_result(ProcessingResult(
                file_path=Path(f"/test/file{i}.mp3"),
                success=True
            ))
        
        # Add failed results
        for i in range(3):
            results.add_result(ProcessingResult(
                file_path=Path(f"/test/error{i}.mp3"),
                success=False,
                error_message="Error"
            ))
        
        assert results.success_rate == 70.0  # 7 successful out of 10 total

    def test_success_rate_zero_files(self):
        """Test success rate with zero total files."""
        results = ProcessingResults(total_files=0)
        assert results.success_rate == 0.0

    def test_error_count_property(self):
        """Test error_count property."""
        results = ProcessingResults(total_files=5)
        
        # Add some errors
        for i in range(3):
            results.add_result(ProcessingResult(
                file_path=Path(f"/test/error{i}.mp3"),
                success=False,
                error_message="Error"
            ))
        
        assert results.error_count == 3


class TestConfigurationSchema:
    """Test cases for ConfigurationSchema dataclass."""

    def test_configuration_schema_defaults(self):
        """Test default values for ConfigurationSchema."""
        config = ConfigurationSchema()
        
        assert config.default_genre == "Unknown"
        assert config.default_year == str(datetime.now().year)
        assert config.music_directory == "~/Music"
        assert config.create_backups is False
        assert config.verbose is False

    def test_configuration_schema_custom_values(self):
        """Test ConfigurationSchema with custom values."""
        config = ConfigurationSchema(
            default_genre="Rock",
            default_year="2020",
            music_directory="/custom/music",
            create_backups=True,
            verbose=True
        )
        
        assert config.default_genre == "Rock"
        assert config.default_year == "2020"
        assert config.music_directory == "/custom/music"
        assert config.create_backups is True
        assert config.verbose is True

    def test_configuration_schema_validation_genre(self):
        """Test validation of default_genre field."""
        with pytest.raises(ValueError, match="default_genre must be a non-empty string"):
            ConfigurationSchema(default_genre="")
        
        with pytest.raises(ValueError, match="default_genre must be a non-empty string"):
            ConfigurationSchema(default_genre="   ")
        
        with pytest.raises(ValueError, match="default_genre must be a non-empty string"):
            ConfigurationSchema(default_genre=123)

    def test_configuration_schema_validation_year(self):
        """Test validation of default_year field."""
        with pytest.raises(ValueError, match="default_year must be a non-empty string"):
            ConfigurationSchema(default_year="")
        
        with pytest.raises(ValueError, match="default_year must be a valid year"):
            ConfigurationSchema(default_year="abc")
        
        with pytest.raises(ValueError, match="default_year must be between 1900"):
            ConfigurationSchema(default_year="1800")
        
        current_year = datetime.now().year
        with pytest.raises(ValueError, match=f"default_year must be between 1900 and {current_year + 10}"):
            ConfigurationSchema(default_year=str(current_year + 20))

    def test_configuration_schema_validation_music_directory(self):
        """Test validation of music_directory field."""
        with pytest.raises(ValueError, match="music_directory must be a non-empty string"):
            ConfigurationSchema(music_directory="")
        
        with pytest.raises(ValueError, match="music_directory must be a non-empty string"):
            ConfigurationSchema(music_directory=123)

    def test_configuration_schema_validation_booleans(self):
        """Test validation of boolean fields."""
        with pytest.raises(ValueError, match="create_backups must be a boolean"):
            ConfigurationSchema(create_backups="true")
        
        with pytest.raises(ValueError, match="verbose must be a boolean"):
            ConfigurationSchema(verbose="false")

    def test_get_music_directory_path(self):
        """Test get_music_directory_path method."""
        config = ConfigurationSchema(music_directory="~/Music")
        path = config.get_music_directory_path()
        
        assert isinstance(path, Path)
        assert path.is_absolute()
        assert "Music" in str(path)

    def test_get_music_directory_path_custom(self):
        """Test get_music_directory_path with custom directory."""
        config = ConfigurationSchema(music_directory="/custom/music/dir")
        path = config.get_music_directory_path()
        
        assert isinstance(path, Path)
        assert str(path) == "/custom/music/dir"