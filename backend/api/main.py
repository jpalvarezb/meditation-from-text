from app.logger import logger
from api.engine import meditation_engine
from fastapi import FastAPI, HTTPException
from api.schemas import MeditationRequest, MeditationResponse
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
    try:
        logger.info("Incoming meditation request...")
        result = await meditation_engine(
            journal_entry=request.journal_entry,
            duration_minutes=request.duration_minutes,
            meditation_type=request.meditation_type,
            mode=request.mode,
        )
        return result
    except Exception as e:
        logger.error(f"API error:{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate meditation")
