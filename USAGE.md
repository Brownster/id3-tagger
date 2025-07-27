# MP3 ID3 Processor - Usage Guide

## Quick Start

The MP3 ID3 Processor is designed to be simple to use. Here are the most common usage scenarios:

### 1. Basic Processing

Process all MP3 files in your ~/Music directory:
```bash
mp3-id3-processor
```

### 2. Preview Changes (Recommended First Step)

Before making any changes, see what the tool would do:
```bash
mp3-id3-processor --dry-run --verbose
```

### 3. Process a Different Directory

If your music is stored elsewhere:
```bash
mp3-id3-processor --directory /path/to/your/music
```

## Step-by-Step Guide

### Step 1: Installation

Install the package using pip:
```bash
pip install .
```

### Step 2: Test Installation

Verify the installation worked:
```bash
mp3-id3-processor --help
```

### Step 3: Preview Mode

Always start with a dry run to see what changes would be made:
```bash
mp3-id3-processor --dry-run --verbose
```

This will show you:
- How many MP3 files were found
- Which files would have a genre added
- Any files that couldn't be processed

### Step 4: Run for Real

If you're happy with the preview, run without `--dry-run`:
```bash
mp3-id3-processor --verbose
```

## Common Scenarios

### Scenario 1: First Time User

```bash
# 1. See what would happen
mp3-id3-processor --dry-run --verbose

# 2. If results look good, process for real
mp3-id3-processor --verbose
```

### Scenario 2: Custom Music Directory

```bash
# Your music is in /media/music instead of ~/Music
mp3-id3-processor --directory /media/music --dry-run --verbose
mp3-id3-processor --directory /media/music --verbose
```

### Scenario 3: No Internet Connection

```bash
# Process without API lookups (uses only existing metadata)
mp3-id3-processor --no-api --verbose
```

### Scenario 4: Large Music Collection

```bash
# Use caching to speed up repeated runs
mp3-id3-processor --cache-dir ./api-cache --verbose
```

## Understanding the Output

### Dry Run Output
```
DRY RUN MODE - No files will be modified
--------------------------------------------------
Would add genre to: song1.mp3 (genre: Rock)
No changes for: song2.mp3 (already has genre)
Would add genre to: song3.mp3 (genre: Pop)
No changes for: song4.mp3 (already has all tags)
```

### Normal Processing Output
```
Starting MP3 ID3 processing...
Found 150 MP3 files to process

[1/150] song1.mp3: Added genre (Rock)
[2/150] song2.mp3: Already had genre
[3/150] song3.mp3: Added genre (Pop)
[4/150] song4.mp3: Already has all tags
```

### Summary Output
```
Processing Summary:
==================
Total files processed: 150
Files modified: 45
Tags added:
  genre: 25 files
Errors: 0
Processing completed successfully!
```

## Configuration Options

### Command Line Options

| Option | Purpose | Example |
|--------|---------|---------|
| `--directory` | Specify music directory | `--directory /media/music` |
| `--dry-run` | Preview changes only | `--dry-run` |
| `--report-missing` | Report files missing genre/year (use with `--dry-run`) | `--dry-run --report-missing` |
| `--verbose` | Show detailed output | `--verbose` |
| `--no-api` | Disable internet lookups | `--no-api` |
| `--config` | Use config file | `--config my-settings.json` |
| `--cache-dir` | Cache API responses | `--cache-dir ./cache` |

### Configuration File

Create a `config.json` file for persistent settings:

```json
{
  "default_genre": "Unknown",
  "music_directory": "~/Music",
  "use_api": true,
  "verbose": true
}
```

Use it with:
```bash
mp3-id3-processor --config config.json
```

## Safety Features

- ✅ Adds missing genre tags
- ✅ Preserves all existing metadata
- ✅ Skips files that already have all tags
- ✅ Provides detailed logging

### What the Tool Never Does
- ❌ Modifies existing tags
- ❌ Changes audio content
- ❌ Deletes or moves files
- ❌ Overwrites existing metadata

## Troubleshooting

### "No MP3 files found"
- Check the directory path: `ls ~/Music`
- Verify MP3 files exist: `find ~/Music -name "*.mp3" | head -5`
- Try a different directory: `--directory /path/to/music`

### "Permission denied"
- Check file permissions: `ls -la ~/Music`
- Ensure you can write to the directory
- Files might be locked by another application

### "API lookup failed"
- Check internet connection
- Try without API: `--no-api`
- Use longer timeout: `--api-timeout 30`

### Files Being Skipped
- Use `--verbose` to see why files are skipped
- Common reasons: already has tags, corrupted file, no metadata for lookup

## Best Practices

### Before First Use
1. **Backup your music collection** (always a good idea)
2. **Run with `--dry-run --verbose`** to preview changes
3. **Test on a small subset** of files first

### Regular Use
1. **Use `--verbose`** to see what's happening
2. **Use `--cache-dir`** for faster repeated runs
3. **Check the summary** to verify expected results

### For Large Collections
1. **Use caching**: `--cache-dir ./cache`
2. **Run during off-peak hours** (API rate limiting)
3. **Monitor progress** with `--verbose`

## Exit Codes

The tool returns different exit codes to indicate success or failure:

- **0**: All files processed successfully
- **1**: All files failed to process
- **2**: Some files processed, some failed
- **130**: Interrupted by user (Ctrl+C)

You can check the exit code in scripts:
```bash
mp3-id3-processor --verbose
if [ $? -eq 0 ]; then
    echo "Processing completed successfully!"
else
    echo "Some errors occurred during processing"
fi
```

## Advanced Usage

### Batch Processing Multiple Directories
```bash
#!/bin/bash
for dir in /media/music1 /media/music2 /media/music3; do
    echo "Processing $dir..."
    mp3-id3-processor --directory "$dir" --verbose
done
```

### Integration with Other Tools
```bash
# Find directories with MP3 files and process each
find /media -name "*.mp3" -exec dirname {} \; | sort -u | while read dir; do
    mp3-id3-processor --directory "$dir"
done
```

### Cron Job for Regular Processing
```bash
# Add to crontab to run weekly
0 2 * * 0 /usr/local/bin/mp3-id3-processor --cache-dir /tmp/mp3-cache
```