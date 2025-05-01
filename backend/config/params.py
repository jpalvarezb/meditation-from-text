import os

# Production // Development
LOG_LEVEL = "DEBUG"  # "INFO" or "DEBUG"

# Local Directories
BASE_ROOT = os.path.dirname(os.path.dirname(__file__))
ASSET_ROOT = os.path.join(BASE_ROOT, "assets")
AUDIO_ROOT = os.path.join(ASSET_ROOT, "audio")
# Audio Directories
SOUNDSCAPES_DIR = os.path.join(AUDIO_ROOT, "soundscapes")
CHIMES_DIR = os.path.join(AUDIO_ROOT, "chimes")
TONES_DIR = os.path.join(AUDIO_ROOT, "tones")
TTS_DIR = os.path.join(AUDIO_ROOT, "tts")
OUTPUT_DIR = os.path.join(AUDIO_ROOT, "output")

# Logging
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


# Secrets
def get_secret(key: str, default=None):
    secret_path = f"/run/secrets/{key}"
    if os.path.exists(secret_path):
        with open(secret_path, "r") as f:
            return f.read().strip()
    return os.getenv(key, default)


GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
