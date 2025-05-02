import os
from openai import OpenAI
from aeneas.task import Task
from datetime import datetime
from aeneas.executetask import ExecuteTask
from config.params import TTS_DIR, OPENAI_API_KEY


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
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
    Use a soft, neutral American accent with no regional inflection.
    Emotional range:
    Keep the emotional expression subtle and steady, avoiding strong emotional peaks.
    Intonation
    Use gentle, downward-sloping intonation to convey peace and reassurance.
    Impressions
    Avoid character impressions; speak authentically and naturally.
    Speed of speech:
    Speak very slowly and evenly. Ensure you take substantial pauses, allowing the listener space to breathe and reflect.
    Tone:
    Use a warm, nurturing tone, as if calmly guiding someone to inner stillness.
    Whispering:
    Do not whisper, but keep the voice soft and close, like a gentle spoken lullaby.
    """,
        response_format="wav",
    ) as response:
        # Save the audio response to created file
        response.stream_to_file(audio_output_path)
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

    return output_json_path
