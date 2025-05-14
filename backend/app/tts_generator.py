import os
from openai import OpenAI
from aeneas.task import Task
from datetime import datetime
from app.logger import logger
from app.cloud_utils import upload_to_gcs
from aeneas.executetask import ExecuteTask
from config.params import TTS_DIR, OPENAI_API_KEY, IS_PROD


openai_client = OpenAI(api_key=OPENAI_API_KEY)


def generate_tts(
    script_text: str,
    voice: str = "sage",
    model: str = "gpt-4o-mini-tts",
):
    """
    Generate TTS audio from meditation script text using Open AI's long-form model.
    Saves as a real WAV file with timestamped filename.
    """

    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    audio_filename = f"tts_audio_{timestamp}.wav"
    audio_output_path = os.path.join(
        TTS_DIR,
        audio_filename,
    )
    # Request TTS audio generation
    with openai_client.audio.speech.with_streaming_response.create(
        input=script_text,
        model=model,
        voice=voice,
        instructions=""""
    Accent:
    Use a soft, neutral British accent with no regional inflection.
    Emotional range:
    Keep the emotional expression subtle and steady, avoiding strong emotional peaks.
    Intonation
    Use gentle, downward-sloping intonation to convey peace and reassurance.
    Impressions
    Avoid character impressions; speak authentically and naturally.
    Speed of speech:
    Speak as slowly and evenly as possible. Ensure you take substantial pauses, allowing the listener space to breathe and reflect.
    Tone:
    Use a warm, nurturing tone, as if calmly guiding someone to inner stillness.
    Whispering:
    Do not whisper, but keep the voice soft and close, like a gentle spoken lullaby.
    """,
        response_format="wav",
    ) as response:
        # Save the audio response to created file
        response.stream_to_file(audio_output_path)
    if IS_PROD:
        gcs_output = upload_to_gcs(local_path=audio_output_path)
        logger.info(f"TTS audio uploaded to GCS: {gcs_output}")
        try:
            os.remove(audio_output_path)
            logger.debug(
                f"Deleted local TTS audio file after upload: {audio_output_path}"
            )
        except Exception as e:
            logger.warning(f"Failed to delete local TTS audio: {e}")
        return gcs_output

    return audio_output_path


def align_audio_text(audio_path: str, text_path: str, output_json_path: str) -> str:
    """
    Aligns audio and text files using Aeneas and outputs a JSON sync map file.
    Returns the path to the generated alignment JSON.
    """
    config_string = "task_language=eng|is_text_type=plain|os_task_file_format=json"

    task = Task(config_string=config_string)
    task.audio_file_path_absolute = audio_path
    task.text_file_path_absolute = text_path
    task.sync_map_file_path_absolute = output_json_path

    ExecuteTask(task).execute()
    task.output_sync_map_file()
    if IS_PROD:
        gcs_output = upload_to_gcs(local_path=output_json_path)
        logger.info(f"Alignment JSON uploaded to GCS: {gcs_output}")
        try:
            os.remove(output_json_path)
            logger.debug(
                f"Deleted local alignment JSON file after upload: {output_json_path}"
            )
        except Exception as e:
            logger.warning(f"Failed to delete local alignment JSON: {e}")
        return gcs_output

    return output_json_path
