"""Unit tests for configuration manager."""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
from mp3_id3_processor.config import Configuration
from mp3_id3_processor.models import ConfigurationSchema


class TestConfiguration:
    """Test cases for Configuration class."""

    def test_configuration_creation_defaults(self):
        """Test Configuration creation with default values."""
        config = Configuration()
        
        assert config.default_genre == "Unknown"
        assert config.default_year == str(ConfigurationSchema().default_year)
        assert str(config.music_directory).endswith("Music")
        assert config.create_backups is False
        assert config.verbose is False

    def test_configuration_creation_with_file(self):
        """Test Configuration creation with config file."""
        config_data = {
            "default_genre": "Rock",
            "default_year": "2020",
            "music_directory": "/custom/music",
            "create_backups": True,
            "verbose": True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = Path(f.name)
        
        try:
            config = Configuration(config_file)
            
            assert config.default_genre == "Rock"
            assert config.default_year == "2020"
            assert str(config.music_directory) == "/custom/music"
            assert config.create_backups is True
            assert config.verbose is True
        finally:
            config_file.unlink()

    def test_configuration_nonexistent_file(self):
        """Test Configuration with non-existent config file."""
        config_file = Path("/nonexistent/config.json")
        config = Configuration(config_file)
        
        # Should fall back to defaults
        assert config.default_genre == "Unknown"
        assert config.default_year == str(ConfigurationSchema().default_year)

    def test_configuration_invalid_json(self):
        """Test Configuration with invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            config_file = Path(f.name)
        
        try:
            with patch('builtins.print') as mock_print:
                config = Configuration(config_file)
                
                # Should fall back to defaults and print warning
                assert config.default_genre == "Unknown"
                mock_print.assert_called()
        finally:
            config_file.unlink()

    def test_configuration_partial_config(self):
        """Test Configuration with partial config file."""
        config_data = {
            "default_genre": "Jazz",
            "verbose": True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = Path(f.name)
        
        try:
            config = Configuration(config_file)
            
            assert config.default_genre == "Jazz"
            assert config.verbose is True
            # Other values should be defaults
            assert config.default_year == str(ConfigurationSchema().default_year)
            assert config.create_backups is False
        finally:
            config_file.unlink()

    def test_configuration_invalid_values(self):
        """Test Configuration with invalid values in config file."""
        config_data = {
            "default_genre": "",  # Invalid empty string
            "default_year": "invalid_year",  # Invalid year
            "create_backups": "not_boolean"  # Invalid boolean
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = Path(f.name)
        
        try:
            with patch('builtins.print') as mock_print:
                config = Configuration(config_file)
                
                # Should fall back to defaults due to validation error
                assert config.default_genre == "Unknown"
                mock_print.assert_called()
        finally:
            config_file.unlink()

    def test_property_access(self):
        """Test property access methods."""
        config_data = {
            "default_genre": "Classical",
            "default_year": "2021",
            "music_directory": "~/MyMusic",
            "create_backups": True,
            "verbose": False
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = Path(f.name)
        
        try:
            config = Configuration(config_file)
            
            assert config.default_genre == "Classical"
            assert config.default_year == "2021"
            assert isinstance(config.music_directory, Path)
            assert "MyMusic" in str(config.music_directory)
            assert config.create_backups is True
            assert config.verbose is False
        finally:
            config_file.unlink()

    @patch('os.access')
    @patch('pathlib.Path.exists')
    def test_validate_success(self, mock_exists, mock_access):
        """Test successful configuration validation."""
        mock_exists.return_value = True
        mock_access.return_value = True
        
        config = Configuration()
        assert config.validate() is True

    @patch('os.access')
    @patch('pathlib.Path.exists')
    def test_validate_directory_not_exists_parent_writable(self, mock_exists, mock_access):
        """Test validation when directory doesn't exist but parent is writable."""
        # First call (music_directory.exists()) returns False
        # Second call (parent.exists()) returns True
        mock_exists.side_effect = [False, True]
        mock_access.return_value = True
        
        config = Configuration()
        assert config.validate() is True

    @patch('os.access')
    @patch('pathlib.Path.exists')
    def test_validate_directory_not_accessible(self, mock_exists, mock_access):
        """Test validation when directory is not accessible."""
        mock_exists.return_value = True
        mock_access.return_value = False
        
        config = Configuration()
        assert config.validate() is False

    @patch('os.access')
    @patch('pathlib.Path.exists')
    def test_validate_parent_not_writable(self, mock_exists, mock_access):
        """Test validation when parent directory is not writable."""
        # First call (music_directory.exists()) returns False
        # Second call (parent.exists()) returns True
        mock_exists.side_effect = [False, True]
        mock_access.return_value = False  # Parent directory is not writable
        
        config = Configuration()
        assert config.validate() is False

    def test_save_to_file(self):
        """Test saving configuration to file."""
        config = Configuration()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir) / "config.json"
            
            result = config.save_to_file(save_path)
            assert result is True
            assert save_path.exists()
            
            # Verify saved content
            with open(save_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['default_genre'] == config.default_genre
            assert saved_data['default_year'] == config.default_year
            assert saved_data['music_directory'] == "~/Music"
            assert saved_data['create_backups'] == config.create_backups
            assert saved_data['verbose'] == config.verbose

    def test_save_to_file_create_parent_directory(self):
        """Test saving configuration creates parent directories."""
        config = Configuration()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            save_path = Path(temp_dir) / "subdir" / "config.json"
            
            result = config.save_to_file(save_path)
            assert result is True
            assert save_path.exists()
            assert save_path.parent.exists()

    @patch('builtins.open', side_effect=OSError("Permission denied"))
    def test_save_to_file_error(self, mock_open):
        """Test save_to_file error handling."""
        config = Configuration()
        save_path = Path("/invalid/path/config.json")
        
        result = config.save_to_file(save_path)
        assert result is False

    def test_get_schema(self):
        """Test get_schema method."""
        config = Configuration()
        schema = config.get_schema()
        
        assert isinstance(schema, ConfigurationSchema)
        assert schema.default_genre == config.default_genre
        assert schema.default_year == config.default_year

    def test_update_from_dict_success(self):
        """Test successful update from dictionary."""
        config = Configuration()
        original_genre = config.default_genre
        
        updates = {
            "default_genre": "Electronic",
            "verbose": True
        }
        
        result = config.update_from_dict(updates)
        assert result is True
        assert config.default_genre == "Electronic"
        assert config.verbose is True
        # Other values should remain unchanged
        assert config.default_year == str(ConfigurationSchema().default_year)

    def test_update_from_dict_invalid_values(self):
        """Test update from dictionary with invalid values."""
        config = Configuration()
        original_genre = config.default_genre
        
        updates = {
            "default_genre": "",  # Invalid empty string
            "default_year": "invalid"
        }
        
        result = config.update_from_dict(updates)
        assert result is False
        # Original values should be preserved
        assert config.default_genre == original_genre

    def test_update_from_dict_partial_update(self):
        """Test partial update from dictionary."""
        config = Configuration()
        original_year = config.default_year
        
        updates = {
            "default_genre": "Hip-Hop"
        }
        
        result = config.update_from_dict(updates)
        assert result is True
        assert config.default_genre == "Hip-Hop"
        assert config.default_year == original_year  # Should remain unchanged

    def test_create_schema_from_dict(self):
        """Test _create_schema_from_dict method."""
        config = Configuration()
        
        config_data = {
            "default_genre": "Pop",
            "default_year": "2022",
            "music_directory": "/music",
            "create_backups": True,
            "verbose": False
        }
        
        schema = config._create_schema_from_dict(config_data)
        
        assert isinstance(schema, ConfigurationSchema)
        assert schema.default_genre == "Pop"
        assert schema.default_year == "2022"
        assert schema.music_directory == "/music"
        assert schema.create_backups is True
        assert schema.verbose is False

    def test_create_schema_from_dict_missing_values(self):
        """Test _create_schema_from_dict with missing values."""
        config = Configuration()
        
        config_data = {
            "default_genre": "Folk"
            # Other values missing
        }
        
        schema = config._create_schema_from_dict(config_data)
        
        assert schema.default_genre == "Folk"
        # Should use defaults for missing values
        assert schema.default_year == str(ConfigurationSchema().default_year)
        assert schema.music_directory == "~/Music"
        assert schema.create_backups is False
        assert schema.verbose is False