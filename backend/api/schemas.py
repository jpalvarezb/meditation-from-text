from pydantic import BaseModel
from typing import Literal


class MeditationRequest(BaseModel):
    journal_entry: str
    duration_minutes: int
    meditation_type: Literal["mindfulness", "visualization", "breathing", "affirmation"]
    mode: Literal["tts", "dev"] = "tts"


class MeditationResponse(BaseModel):
    final_audio_path: str
    emotion_summary: dict
    script_path: str
    tts_path: str
    alignment_path: str
