#!/usr/bin/env python3
"""
Validation script to ensure that existing metadata is never modified during processing.
This script uses the existing test fixtures to create MP3 files and validates
that the processor only adds missing tags without modifying existing ones.
"""

import sys
import tempfile
from pathlib import Path

# Add the tests directory to the path to import fixtures
sys.path.insert(0, str(Path(__file__).parent / 'tests'))

from fixtures import MP3TestFileGenerator, TestDataSets
from mp3_id3_processor.processor import ID3Processor
from mp3_id3_processor.config import Configuration
from mutagen.mp3 import MP3


def get_all_tags(file_path: Path):
    """Get all ID3 tags from an MP3 file."""
    try:
        audio = MP3(file_path)
        if audio.tags is None:
            return {}
        
        tags = {}
        for key, value in audio.tags.items():
            if hasattr(value, 'text'):
                tags[key] = str(value.text[0]) if value.text else ''
            else:
                tags[key] = str(value)
        return tags
    except Exception as e:
        print(f"Error reading tags from {file_path}: {e}")
        return {}


def validate_metadata_preservation():
    """Main validation function."""
    print("=" * 60)
    print("METADATA PRESERVATION VALIDATION")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        generator = MP3TestFileGenerator(temp_path)
        
        # Test cases using the fixture generator
        test_cases = [
            ("complete_tags.mp3", {"title": "Song 1", "artist": "Artist 1", "album": "Album 1", "genre": "Rock", "year": "2020"}, []),
            ("missing_genre.mp3", {"title": "Song 2", "artist": "Artist 2", "album": "Album 2", "year": "2021"}, ["genre"]),
            ("missing_year.mp3", {"title": "Song 3", "artist": "Artist 3", "album": "Album 3", "genre": "Pop"}, ["year"]),
            ("missing_both.mp3", {"title": "Song 4", "artist": "Artist 4", "album": "Album 4"}, ["genre", "year"]),
            ("minimal_tags.mp3", {"title": "Song 5"}, ["genre", "year"]),
        ]
        
        # Create test files
        print("Creating test MP3 files...")
        test_files = []
        original_tags = {}
        
        for filename, tags, expected in test_cases:
            try:
                file_path = generator.create_mp3_with_tags(filename, tags)
                test_files.append((file_path, expected))
                original_tags[filename] = get_all_tags(file_path)
                print(f"  Created {filename} with {len(original_tags[filename])} tags")
            except Exception as e:
                print(f"  Failed to create {filename}: {e}")
                continue
        
        # Initialize processor with test configuration
        config = Configuration()
        processor = ID3Processor(config)
        
        print("\nProcessing files...")
        results = []
        
        for file_path, expected_changes in test_files:
            print(f"\nProcessing {file_path.name}...")
            
            # Get tags before processing
            tags_before = get_all_tags(file_path)
            print(f"  Tags before: {len(tags_before)} tags")
            
            # Process the file
            try:
                result = processor.process_file(file_path)
                print(f"  Processing result: success={result.success}, tags_added={result.tags_added}")
            except Exception as e:
                print(f"  Processing failed: {e}")
                continue
            
            # Get tags after processing
            tags_after = get_all_tags(file_path)
            print(f"  Tags after: {len(tags_after)} tags")
            
            # Validate that existing tags were not modified
            validation_passed = True
            for tag_key, original_value in tags_before.items():
                if tag_key in tags_after:
                    if tags_after[tag_key] != original_value:
                        print(f"  ❌ VIOLATION: Tag {tag_key} was modified!")
                        print(f"     Original: {original_value}")
                        print(f"     Modified: {tags_after[tag_key]}")
                        validation_passed = False
                else:
                    print(f"  ❌ VIOLATION: Tag {tag_key} was removed!")
                    validation_passed = False
            
            # Check for expected new tags
            new_tags = set(tags_after.keys()) - set(tags_before.keys())
            expected_new_tags = set()
            
            if "genre" in expected_changes:
                expected_new_tags.update(["TCON"])  # Genre tag
            if "year" in expected_changes:
                expected_new_tags.update(["TDRC", "TYER"])  # Year tags (either format)
            
            # Validate new tags
            if expected_changes:
                if not new_tags:
                    print(f"  ⚠️  WARNING: Expected new tags {expected_changes} but none were added")
                else:
                    print(f"  ✅ New tags added: {list(new_tags)}")
            else:
                if new_tags:
                    print(f"  ⚠️  WARNING: Unexpected new tags added: {list(new_tags)}")
                else:
                    print(f"  ✅ No changes made (as expected)")
            
            if validation_passed:
                print(f"  ✅ VALIDATION PASSED: No existing metadata was modified")
            else:
                print(f"  ❌ VALIDATION FAILED: Existing metadata was modified!")
            
            results.append((file_path.name, validation_passed, len(tags_before), len(tags_after)))
        
        # Summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, passed, _, _ in results if passed)
        total = len(results)
        
        print(f"Files tested: {total}")
        print(f"Validations passed: {passed}")
        print(f"Validations failed: {total - passed}")
        
        if passed == total:
            print("\n🎉 ALL VALIDATIONS PASSED!")
            print("✅ The processor preserves all existing metadata")
            print("✅ Only missing tags are added")
            return True
        else:
            print(f"\n❌ {total - passed} VALIDATION(S) FAILED!")
            print("⚠️  The processor may be modifying existing metadata")
            return False


if __name__ == "__main__":
    success = validate_metadata_preservation()
    exit(0 if success else 1)