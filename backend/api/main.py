import uuid
import tempfile
import os
from app.logger import logger
from api.engine import meditation_engine
from fastapi import FastAPI, HTTPException, Depends, Header
from api.schemas import (
    MeditationRequest,
    MeditationResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from app.cache_utils import (
    generate_cache_key,
    save_to_cache,
    load_from_cache,
)

from fastapi.middleware.cors import CORSMiddleware
from config.params import API_KEY

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://minday-project.web.app/", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/meditate", response_model=MeditationResponse)
async def meditate(
    api_key: str = Header(None, alias="x-api-key"),
    body: MeditationRequest = Depends(),
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")

    cache_key = generate_cache_key(
        body.journal_entry, body.duration_minutes, body.meditation_type
    )

    cached = load_from_cache(cache_key)
    if cached:
        logger.info("Serving meditation from cache")
        return cached

    request_id = str(uuid.uuid4())
    tmp_root = os.path.join(tempfile.gettempdir(), f"minday-{request_id}")
    os.makedirs(tmp_root, exist_ok=True)

    try:
        result = await meditation_engine(
            journal_entry=body.journal_entry,
            duration_minutes=body.duration_minutes,
            meditation_type=body.meditation_type,
            mode=body.mode,
            tmp_root=tmp_root,
        )
    except ValueError as e:
        if str(e) == "threshold_unmet":
            return MeditationResponse(status="error", reason="threshold_unmet")
        raise HTTPException(status_code=500, detail="Failed to generate script")
    except Exception as e:
        logger.error(f"API error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate meditation")

    # Cache only raw GCS paths and emotion summary, omitting final_signed_url
    to_cache = {
        "final_audio_path": result["final_audio_path"],
        "emotion_summary": result["emotion_summary"],
        "script_path": result["script_path"],
        "tts_path": result["tts_path"],
        "alignment_path": result["alignment_path"],
    }
    save_to_cache(cache_key, to_cache)
    return result


@app.post("/feedback", response_model=FeedbackResponse)
async def feedback(feedback: FeedbackRequest):
    try:
        logger.info(f"User feedback:{feedback.model_dump()}")
        return FeedbackResponse(
            message="Thank you. Feedback received", status="success"
        )
    except Exception as e:
        logger.exception(f"Failed to process feedback: {e}")
        return FeedbackResponse(
            message="Failed to process feedback. Please try again later.",
            status="error",
        )
