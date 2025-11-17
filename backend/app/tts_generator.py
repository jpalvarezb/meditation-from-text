import os
from datetime import datetime
from openai import OpenAI
from app.logger import logger
from app.cloud_utils import upload_to_gcs
from config.params import OPENAI_API_KEY, IS_PROD

# Optional aeneas import for local dev convenience
try:
    from aeneas.task import Task
    from aeneas.executetask import ExecuteTask
    AENEAS_AVAILABLE = True
except Exception:
    AENEAS_AVAILABLE = False

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def generate_tts(
    script_path: str,
    voice: str = "sage",
    model: str = "gpt-4o-mini-tts",
    tmp_root: str = "/tmp",
) -> str:
    """
    Generate TTS audio from a local script file. Writes the .wav into tmp_root with a unique filename.
    In production (IS_PROD=True), uploads to GCS, deletes the local copy, and returns the GCS URI.
    In dev mode, simply returns the local path under tmp_root.
    """
    # --- Read the script from disk (script_path is already a local file) ---
    with open(script_path, "r") as f:
        script_text = f.read()

    # --- Ensure tmp_root exists ---
    os.makedirs(tmp_root, exist_ok=True)

    # --- Create a timestamped filename under tmp_root ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    audio_filename = f"tts_audio_{timestamp}.wav"
    audio_output_path = os.path.join(tmp_root, audio_filename)

    # --- Generate TTS via OpenAI ---
    with openai_client.audio.speech.with_streaming_response.create(
        input=script_text,
        model=model,
        voice=voice,
        speed=0.96,
        instructions="""
        Voice: Use a soft, neutral British accent with no regional inflection.

        Tone: Peaceful. Keep the emotional expression subtle and steady, avoiding strong emotional peaks.

        Delivery: Calm, slow, and collected. Speak as slowly and evenly as possible.
        Ensure you take substantial pauses, allowing the listener space to breathe and reflect.

        Pronunciation: Soft and close, like a gentle spoken lullaby.
        """,
        response_format="wav",
    ) as response:
        # Stream the resulting WAV into our tmp_root file
        response.stream_to_file(audio_output_path)

    if IS_PROD:
        # Upload the local .wav to GCS, then delete the local copy
        gcs_uri = upload_to_gcs(
            local_path=audio_output_path, dest_path=f"tts/{audio_filename}"
        )
        logger.info(f"TTS audio uploaded to GCS: {gcs_uri}")
        try:
            os.remove(audio_output_path)
            logger.debug(f"Deleted local TTS file: {audio_output_path}")
        except Exception as e:
            logger.warning(f"Could not delete local TTS file {audio_output_path}: {e}")
        return gcs_uri

    # In dev mode, return the local tmp_root path
    return audio_output_path


def align_audio_text(
    audio_path: str,
    text_path: str,
    tmp_root: str = "/tmp",
) -> str:
    """
    Run Aeneas alignment between a local audio file and a local text file.
    Creates a JSON alignment in tmp_root. In production, uploads to GCS & deletes local.
    Returns either the local JSON path (dev) or the GCS URI (prod).
    If aeneas is not available locally, raise a clear error recommending Docker.
    """
    if not AENEAS_AVAILABLE:
        raise RuntimeError(
            "Aeneas is not installed in this environment. Run the backend via Docker (compose) or install aeneas as documented."
        )

    # --- Ensure tmp_root exists ---
    os.makedirs(tmp_root, exist_ok=True)

    # --- Build a timestamped output filename under tmp_root ---
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    alignment_filename = f"alignment_{timestamp}.json"
    alignment_output_path = os.path.join(tmp_root, alignment_filename)

    # --- Configure and run Aeneas ---
    config_string = "task_language=eng|is_text_type=plain|os_task_file_format=json"
    task = Task(config_string=config_string)

    # audio_path and text_path are already local paths
    task.audio_file_path_absolute = audio_path
    task.text_file_path_absolute = text_path
    task.sync_map_file_path_absolute = alignment_output_path

    ExecuteTask(task).execute()
    task.output_sync_map_file()

    if IS_PROD:
        # Upload the JSON to GCS, delete local copy
        gcs_uri = upload_to_gcs(
            local_path=alignment_output_path, dest_path=f"tts/{alignment_filename}"
        )
        logger.info(f"Alignment JSON uploaded to GCS: {gcs_uri}")
        try:
            os.remove(alignment_output_path)
        except Exception as e:
            logger.warning(
                f"Could not delete local alignment JSON {alignment_output_path}: {e}"
            )
        return gcs_uri

    # In dev, just return the local tmp_root path
    return alignment_output_path
