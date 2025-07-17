#!/usr/bin/env python3
"""
Performance test script to validate the MP3 ID3 processor with larger collections.
This script creates a collection of test MP3 files and measures processing performance.
"""

import sys
import time
import tempfile
from pathlib import Path

# Add the tests directory to the path to import fixtures
sys.path.insert(0, str(Path(__file__).parent / 'tests'))

from fixtures import MP3TestFileGenerator
from mp3_id3_processor.processor import ID3Processor
from mp3_id3_processor.config import Configuration
from mp3_id3_processor.scanner import FileScanner
from mp3_id3_processor.logger import ProcessingLogger
from mp3_id3_processor.models import ProcessingResults


def create_large_test_collection(generator: MP3TestFileGenerator, num_files: int = 100):
    """Create a large collection of test MP3 files."""
    print(f"Creating {num_files} test MP3 files...")
    
    files = []
    tag_variations = [
        {"title": "Song {}", "artist": "Artist {}", "album": "Album {}", "genre": "Rock", "year": "2020"},
        {"title": "Track {}", "artist": "Band {}", "album": "Record {}", "year": "2021"},  # Missing genre
        {"title": "Tune {}", "artist": "Musician {}", "album": "Collection {}", "genre": "Pop"},  # Missing year
        {"title": "Music {}", "artist": "Performer {}", "album": "Compilation {}"},  # Missing both
        {"title": "Song {}", "artist": "Artist {}", "album": "Album {}", "genre": "Jazz", "year": "2022"},  # Complete
    ]
    
    start_time = time.time()
    
    for i in range(num_files):
        variation = tag_variations[i % len(tag_variations)]
        tags = {}
        for key, value in variation.items():
            if "{}" in value:
                tags[key] = value.format(i + 1)
            else:
                tags[key] = value
        
        filename = f"test_song_{i+1:03d}.mp3"
        try:
            file_path = generator.create_mp3_with_tags(filename, tags)
            files.append(file_path)
            
            if (i + 1) % 20 == 0:
                print(f"  Created {i + 1}/{num_files} files...")
        except Exception as e:
            print(f"  Failed to create {filename}: {e}")
    
    creation_time = time.time() - start_time
    print(f"Created {len(files)} files in {creation_time:.2f} seconds")
    
    return files


def test_processing_performance(tmp_path: Path, num_files: int = 100):
    music_dir = tmp_path
    """Test processing performance with a large collection."""
    print("=" * 60)
    print(f"PERFORMANCE TEST - {num_files} FILES")
    print("=" * 60)
    
    # Create test collection
    generator = MP3TestFileGenerator(music_dir)
    files = create_large_test_collection(generator, num_files)
    
    if not files:
        print("❌ No test files created, aborting performance test")
        return False
    
    # Initialize components
    config = Configuration()
    scanner = FileScanner()
    processor = ID3Processor(config)
    logger = ProcessingLogger(verbose=False)  # Reduce verbosity for performance test
    
    print(f"\nStarting performance test with {len(files)} files...")
    
    # Measure scanning performance
    print("\n1. Testing file scanning performance...")
    scan_start = time.time()
    try:
        scanned_files = scanner.scan_directory(music_dir)
        scan_time = time.time() - scan_start
        print(f"   Scanned {len(scanned_files)} files in {scan_time:.3f} seconds")
        print(f"   Scanning rate: {len(scanned_files)/scan_time:.1f} files/second")
    except Exception as e:
        print(f"   ❌ Scanning failed: {e}")
        return False
    
    # Measure processing performance
    print("\n2. Testing processing performance...")
    results = ProcessingResults(total_files=len(scanned_files))
    
    process_start = time.time()
    processed_count = 0
    modified_count = 0
    error_count = 0
    
    for i, file_path in enumerate(scanned_files):
        try:
            result = processor.process_file(file_path)
            results.add_result(result)
            processed_count += 1
            
            if result.tags_added:
                modified_count += 1
            
            # Progress reporting for large collections
            if (i + 1) % 25 == 0:
                elapsed = time.time() - process_start
                rate = (i + 1) / elapsed
                print(f"   Processed {i + 1}/{len(scanned_files)} files ({rate:.1f} files/sec)")
                
        except Exception as e:
            error_count += 1
            print(f"   Error processing {file_path.name}: {e}")
    
    process_time = time.time() - process_start
    
    # Performance summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"Total files: {len(scanned_files)}")
    print(f"Files processed: {processed_count}")
    print(f"Files modified: {modified_count}")
    print(f"Processing errors: {error_count}")
    print(f"Processing time: {process_time:.3f} seconds")
    print(f"Processing rate: {processed_count/process_time:.1f} files/second")
    print(f"Success rate: {(processed_count/(processed_count + error_count))*100:.1f}%")
    
    # Memory and efficiency metrics
    avg_time_per_file = process_time / processed_count if processed_count > 0 else 0
    print(f"Average time per file: {avg_time_per_file*1000:.1f} milliseconds")
    
    # Performance benchmarks
    print("\n" + "-" * 40)
    print("PERFORMANCE BENCHMARKS")
    print("-" * 40)
    
    files_per_second = processed_count / process_time if process_time > 0 else 0
    
    if files_per_second >= 50:
        print("🚀 EXCELLENT: Very fast processing (50+ files/sec)")
    elif files_per_second >= 20:
        print("✅ GOOD: Fast processing (20+ files/sec)")
    elif files_per_second >= 10:
        print("👍 ACCEPTABLE: Moderate processing (10+ files/sec)")
    elif files_per_second >= 5:
        print("⚠️  SLOW: Below optimal performance (5+ files/sec)")
    else:
        print("❌ VERY SLOW: Performance needs improvement (<5 files/sec)")
    
    if error_count == 0:
        print("✅ RELIABILITY: No processing errors")
    elif error_count < processed_count * 0.05:  # Less than 5% error rate
        print("👍 RELIABILITY: Low error rate (<5%)")
    else:
        print("⚠️  RELIABILITY: High error rate (>5%)")
    
    # Test with dry run mode for comparison
    print("\n3. Testing dry-run performance...")
    dry_run_start = time.time()
    
    # Simulate dry run processing (just analysis, no file modification)
    dry_run_count = 0
    for file_path in scanned_files[:min(50, len(scanned_files))]:  # Test subset for dry run
        try:
            # Just load and analyze the file without modification
            audio_file = processor._load_mp3_file(file_path)
            if audio_file:
                processor.needs_genre_tag(audio_file)
                processor.needs_year_tag(audio_file)
                dry_run_count += 1
        except Exception:
            pass
    
    dry_run_time = time.time() - dry_run_start
    dry_run_rate = dry_run_count / dry_run_time if dry_run_time > 0 else 0
    
    print(f"   Dry-run processed {dry_run_count} files in {dry_run_time:.3f} seconds")
    print(f"   Dry-run rate: {dry_run_rate:.1f} files/second")
    
    return error_count == 0 and files_per_second >= 5  # Minimum acceptable performance


def main():
    """Main performance test function."""
    print("MP3 ID3 Processor - Performance Test")
    print("=" * 60)
    
    # Test with different collection sizes
    test_sizes = [50, 100]  # Start with smaller sizes for validation
    
    all_passed = True
    
    for size in test_sizes:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            try:
                passed = test_processing_performance(temp_path, size)
                if not passed:
                    all_passed = False
                    print(f"❌ Performance test with {size} files FAILED")
                else:
                    print(f"✅ Performance test with {size} files PASSED")
                    
            except Exception as e:
                print(f"❌ Performance test with {size} files FAILED: {e}")
                all_passed = False
            
            print("\n" + "=" * 60 + "\n")
    
    if all_passed:
        print("🎉 ALL PERFORMANCE TESTS PASSED!")
        print("✅ The processor handles large collections efficiently")
        return True
    else:
        print("❌ SOME PERFORMANCE TESTS FAILED!")
        print("⚠️  Performance may need optimization for large collections")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)