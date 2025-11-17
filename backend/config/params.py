import os

## Production // Development
LOG_LEVEL = "DEBUG"  # "INFO" or "DEBUG"
ENV = os.getenv("ENV", "local")  # fallback to local if not set
LOCAL_TEST = os.getenv("LOCAL_TEST", "false")
IS_LOCAL_TEST = LOCAL_TEST.lower() == "true"
IS_PROD = ENV == "prod"

# Local Directories
BASE_ROOT = os.path.dirname(os.path.dirname(__file__))
ASSET_ROOT = os.path.join(BASE_ROOT, "assets")
AUDIO_ROOT = os.path.join(ASSET_ROOT, "audio")
CACHE_DIR = "/tmp/meditation_cache" if IS_PROD else os.path.join(ASSET_ROOT, "cache")
# Audio Directories
SOUNDSCAPES_DIR = os.path.join(AUDIO_ROOT, "soundscapes")
CHIMES_DIR = os.path.join(AUDIO_ROOT, "chimes")
TONES_DIR = os.path.join(AUDIO_ROOT, "tones")
TTS_DIR = os.path.join(AUDIO_ROOT, "tts")

# Output Directory
if IS_PROD:
    OUTPUT_DIR = "/tmp/output"
else:
    OUTPUT_DIR = os.path.join(AUDIO_ROOT, "output")

# Logging
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


# Get Secret function (Docker Compose Architecture)
def get_secret(key: str, default=None):
    secret_path = f"/run/secrets/{key}"
    if os.path.exists(secret_path):
        with open(secret_path, "r") as f:
            return f.read().strip()
    return os.getenv(key, default)


## Google Services
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
GCP_PROJECT_ID = os.getenv("PROJECT_ID", "minday-project")
GCP_AUDIO_BUCKET = os.getenv("AUDIO_BUCKET", "minday-audio")
GCP_AUDIO_BUCKET_REGION = os.getenv("AUDIO_BUCKET_REGION", "northamerica-south1")

## Amazon Web Services
AWS_ACCESS_KEY_ID = get_secret("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = get_secret("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "us-east-1"

## OpenAI
OPENAI_API_KEY = get_secret("OPENAI_API_KEY")

## Backend
# Accept either BACKEND_API_KEY (preferred) or API_KEY
API_KEY = os.getenv("BACKEND_API_KEY") or os.getenv("API_KEY")
