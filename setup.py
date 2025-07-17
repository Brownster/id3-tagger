"""Setup configuration for MP3 ID3 Processor."""

from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mp3-id3-processor",
    version="1.0.0",
    author="MP3 ID3 Processor",
    description="Automatically add missing genre and year ID3 tags to MP3 files",
    long_description="A simple command-line tool that scans MP3 files in the ~/Music directory and adds missing genre and year ID3 tags without modifying existing metadata.",
    long_description_content_type="text/plain",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "mp3-id3-processor=mp3_id3_processor.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Utilities",
    ],
)