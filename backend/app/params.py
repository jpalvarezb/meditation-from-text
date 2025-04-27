import os

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Local Directories
SOUNDSCAPES_DIR = os.getenv("SOUNDSCAPES_DIR", "audio/soundscapes/")
CHIMES_DIR = os.getenv("CHIMES_DIR", "audio/chimes/")
TONES_DIR = os.getenv("TONES_DIR", "audio/tones/")
TTS_DIR = os.getenv("TTS_DIR", "audio/tts/")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "audio/output/")
