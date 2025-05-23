from app.logger import logger
from api.engine import meditation_engine
from fastapi import FastAPI, HTTPException
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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/meditate", response_model=MeditationResponse)
async def meditate(request: MeditationRequest):
    cache_key = generate_cache_key(
        request.journal_entry, request.duration_minutes, request.meditation_type
    )

    # 1) Try cache
    cached = load_from_cache(cache_key)
    if cached:
        logger.info("Serving meditation from cache")
        return cached

    # 2) Compute
    try:
        result = await meditation_engine(
            journal_entry=request.journal_entry,
            duration_minutes=request.duration_minutes,
            meditation_type=request.meditation_type,
            mode=request.mode,
        )
    except ValueError as e:
        if str(e) == "threshold_unmet":
            return MeditationResponse(
                status="error",
                reason="threshold_unmet",
            )
        raise HTTPException(status_code=500, detail="Failed to generate script")
    except Exception as e:
        logger.error(f"API error:{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate meditation")

    # 3) Save to cache (local → GCS), then return
    save_to_cache(cache_key, result)
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
