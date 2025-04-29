import os

# Local Directories
AUDIO_ROOT = os.path.join(os.path.expanduser("~"), "audio-assets")
SOUNDSCAPES_DIR = os.path.join(AUDIO_ROOT, "soundscapes")
CHIMES_DIR = os.path.join(AUDIO_ROOT, "chimes")
TONES_DIR = os.path.join(AUDIO_ROOT, "tones")
TTS_DIR = os.path.join(AUDIO_ROOT, "tts")
OUTPUT_DIR = os.path.join(AUDIO_ROOT, "output")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
