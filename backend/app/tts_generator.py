import re
import boto3
from aeneas.task import Task
from aeneas.executetask import ExecuteTask
from config.calm_triggers import CALM_TRIGGERS


def text_to_ssml(script: str) -> str:
    """
    Converts a meditation script to SSML with:
    - <s> for sentence separation
    - <break time="2s"/> for calming trigger words
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


def amazon_tts(
    ssml_text: str,
    output_path: str,
    voice_id: str = "Ruth",
    output_format: str = "mp3",
    engine: str = "long-form",
) -> str:
    """
    Generate TTS audio using Amazon Polly's long-form model with SSML.
    """
    polly = boto3.client("polly")

    response = polly.synthesize_speech(
        Text=ssml_text,
        TextType="ssml",
        VoiceId=voice_id,
        OutputFormat=output_format,
        Engine=engine,
    )

    with open(output_path, "wb") as file:
        file.write(response["AudioStream"].read())

    return output_path


def align_audio_text(audio_path: str, text_path: str, output_json_path: str):
    """
    Aligns audio and text files using Aeneas and outputs a JSON file."""
    config_string = "task_language=eng|is_text_type=plain|os_task_file_format=json"

    task = Task(config_string=config_string)
    task.audio_file_path_absolute = audio_path
    task.text_file_path_absolute = text_path
    task.sync_map_file_path_absolute = output_json_path

    ExecuteTask(task).execute()
    task.output_sync_map_file()

    return None
