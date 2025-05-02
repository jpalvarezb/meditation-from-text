import re
import os
import wave
import boto3
from aeneas.task import Task
from datetime import datetime
from aeneas.executetask import ExecuteTask
from config.params import TTS_DIR, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
from config.calm_triggers import CALM_TRIGGERS


def text_to_ssml(script: str) -> str:
    """
    Converts a meditation script to SSML with:
    - <s> for sentence separation
    - <break time="2.8s"/> for calming trigger words
    - <prosody rate="80%"> to slow down speech
    - Proper XML escaping
    """
    processed = ["<speak>", '<prosody rate="80%">']

    lines = [line.strip() for line in script.strip().splitlines() if line.strip()]
    for line in lines:
        sentences = re.split(r"(?<=[.!?])\s+", line)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if any(trigger in sentence.lower() for trigger in CALM_TRIGGERS):
                processed.append(sentence)
                processed.append('<break time="2.8s"/>')
            else:
                processed.append(f"<s>{sentence}</s>")

    processed.append("</prosody>")
    processed.append("</speak>")
    return "\n".join(processed)


def generate_tts(
    script_text: str,
    voice_id: str = "Ruth",
    engine: str = "long-form",
    sample_rate: int = 16000,
) -> str:
    """
    Generate TTS audio from meditation script text using Amazon Polly's long-form model.
    Saves as a real WAV file with timestamped filename.
    """
    # Initialize Polly client
    polly = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    ).client("polly")

    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_filename = f"generated_{timestamp}.wav"
    audio_output_path = os.path.join(TTS_DIR, audio_filename)

    # Build SSML
    ssml_text = text_to_ssml(script_text)

    # Request PCM audio stream
    response = polly.synthesize_speech(
        Text=ssml_text,
        TextType="ssml",
        OutputFormat="pcm",
        SampleRate=str(sample_rate),  # Polly expects SampleRate as string
        VoiceId=voice_id,
        Engine=engine,
    )

    # Safety check
    audio_stream = response.get("AudioStream")
    if audio_stream is None:
        raise RuntimeError("Polly returned no audio stream.")

    pcm_data = audio_stream.read()

    # Wrap raw PCM into proper WAV
    with wave.open(audio_output_path, "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit audio (2 bytes)
        wav_file.setframerate(sample_rate)  # 16 kHz or whatever you set
        wav_file.writeframes(pcm_data)

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
