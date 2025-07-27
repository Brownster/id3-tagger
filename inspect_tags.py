
from mp3_id3_processor.processor import ID3Processor
from mp3_id3_processor.config import Configuration
from pathlib import Path

config = Configuration()
processor = ID3Processor(config)
tags = processor.get_existing_tags(Path("/home/marc/Downloads/id3-tagger/Fugees/The Score (Expanded Edition)/04 - Zealots.mp3"))
print(tags)
