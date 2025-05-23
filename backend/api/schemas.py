from pydantic import BaseModel
from typing import Literal


class MeditationRequest(BaseModel):
    journal_entry: str
    duration_minutes: int
    meditation_type: Literal[
        "morning",
        "evening",
        "sleep",
        "stress release",
        "conflict resolution",
        "self-love",
        "focus reset",
    ]
    mode: Literal["tts", "dev"] = "tts"


class MeditationResponse(BaseModel):
    final_signed_url: str
    final_audio_path: str
    emotion_summary: dict
    script_path: str
    tts_path: str
    alignment_path: str


class FeedbackRequest(BaseModel):
    star_rating: int
    feedback_text: str


class FeedbackResponse(BaseModel):
    message: str
    status: str
