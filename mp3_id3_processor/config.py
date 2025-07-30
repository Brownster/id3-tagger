"""Configuration manager for application settings."""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from .models import ConfigurationSchema


class Configuration:
    """Configuration manager for loading and accessing application settings."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize configuration with optional config file.
        
        Args:
            config_file: Optional path to configuration file. If None, uses defaults.
        """
        self._config_file = config_file
        self._schema = self._load_configuration()
    
    def _load_configuration(self) -> ConfigurationSchema:
        """Load configuration from file or use defaults.
        
        Returns:
            ConfigurationSchema instance with loaded or default values.
        """
        if self._config_file and self._config_file.exists():
            try:
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return self._create_schema_from_dict(config_data)
            except (json.JSONDecodeError, OSError, ValueError) as e:
                # Log warning and fall back to defaults
                print(f"Warning: Could not load configuration from {self._config_file}: {e}")
                print("Using default configuration values.")
                return ConfigurationSchema()
        else:
            return ConfigurationSchema()
    
    def _create_schema_from_dict(self, config_data: Dict[str, Any]) -> ConfigurationSchema:
        """Create ConfigurationSchema from dictionary data.
        
        Args:
            config_data: Dictionary containing configuration values.
            
        Returns:
            ConfigurationSchema instance with validated values.
        """
        # Extract values with defaults
        music_directory = config_data.get('music_directory', '~/Music')
        create_backups = config_data.get('create_backups', False)
        verbose = config_data.get('verbose', False)
        use_api = config_data.get('use_api', True)
        api_timeout = config_data.get('api_timeout', 10.0)
        api_cache_dir = config_data.get('api_cache_dir', None)
        api_request_delay = config_data.get('api_request_delay', 0.5)
        default_genre = config_data.get('default_genre', None)
        default_year = config_data.get('default_year', None)
        original_release_date = config_data.get('original_release_date', True)
        
        return ConfigurationSchema(
            music_directory=music_directory,
            create_backups=create_backups,
            verbose=verbose,
            use_api=use_api,
            api_timeout=api_timeout,
            api_cache_dir=api_cache_dir,
            api_request_delay=api_request_delay,
            default_genre=default_genre,
            default_year=default_year,
            original_release_date=original_release_date
        )
    
    @property
    def music_directory(self) -> Path:
        """Get music directory path as Path object."""
        return self._schema.get_music_directory_path()
    
    @property
    def create_backups(self) -> bool:
        """Get create_backups setting."""
        return self._schema.create_backups
    
    @property
    def verbose(self) -> bool:
        """Get verbose setting."""
        return self._schema.verbose
    
    @property
    def use_api(self) -> bool:
        """Get use_api setting."""
        return self._schema.use_api
    
    @property
    def api_timeout(self) -> float:
        """Get API timeout setting."""
        return self._schema.api_timeout
    
    @property
    def api_cache_dir(self) -> Optional[str]:
        """Get API cache directory setting."""
        return self._schema.api_cache_dir
    
    @property
    def api_request_delay(self) -> float:
        """Get API request delay setting."""
        return self._schema.api_request_delay
    
    @property
    def default_genre(self) -> Optional[str]:
        """Get default genre setting."""
        return self._schema.default_genre
    
    @property
    def default_year(self) -> Optional[str]:
        """Get default year setting."""
        return self._schema.default_year
    
    @property
    def original_release_date(self) -> bool:
        """Get original release date preference setting."""
        return self._schema.original_release_date
    
    def validate(self) -> bool:
        """Validate current configuration.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        try:
            # Check if music directory exists or can be created
            music_dir = self.music_directory
            if not music_dir.exists():
                # Check if parent directory exists and is writable
                parent = music_dir.parent
                if not parent.exists() or not os.access(parent, os.W_OK):
                    return False
            elif not os.access(music_dir, os.R_OK):
                return False
            
            return True
        except (OSError, ValueError):
            return False
    
    def save_to_file(self, file_path: Path) -> bool:
        """Save current configuration to file.
        
        Args:
            file_path: Path where to save the configuration.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            config_dict = {
                'music_directory': str(self._schema.music_directory),  # Use original string
                'create_backups': self.create_backups,
                'verbose': self.verbose,
                'use_api': self.use_api,
                'api_timeout': self.api_timeout,
                'api_cache_dir': self.api_cache_dir,
                'api_request_delay': self.api_request_delay,
                'default_genre': self.default_genre,
                'default_year': self.default_year,
                'original_release_date': self.original_release_date
            }
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2)
            
            return True
        except (OSError, ValueError):
            return False
    
    def get_schema(self) -> ConfigurationSchema:
        """Get the underlying configuration schema.
        
        Returns:
            ConfigurationSchema instance.
        """
        return self._schema
    
    def update_from_dict(self, updates: Dict[str, Any]) -> bool:
        """Update configuration from dictionary.
        
        Args:
            updates: Dictionary containing configuration updates.
            
        Returns:
            True if update was successful, False otherwise.
        """
        try:
            # Create new schema with updated values
            current_dict = {
                'music_directory': str(self._schema.music_directory),
                'create_backups': self.create_backups,
                'verbose': self.verbose,
                'use_api': self.use_api,
                'api_timeout': self.api_timeout,
                'api_cache_dir': self.api_cache_dir,
                'api_request_delay': self.api_request_delay,
                'default_genre': self.default_genre,
                'default_year': self.default_year,
                'original_release_date': self.original_release_date
            }
            
            # Apply updates
            current_dict.update(updates)
            
            # Create new schema (this will validate the values)
            new_schema = self._create_schema_from_dict(current_dict)
            
            # If validation passes, update the schema
            self._schema = new_schema
            return True
        except ValueError:
            return False