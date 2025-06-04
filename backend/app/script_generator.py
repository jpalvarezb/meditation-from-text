import os
import asyncio
from google import genai
from datetime import datetime
from app.logger import logger
from config.params import GEMINI_API_KEY, IS_PROD
from google.genai.errors import ServerError, ClientError
from config.meditation_types import MEDITATION_TYPE_STYLES
from app.cloud_utils import upload_to_gcs
from config.emotion_techniques import (
    EMOTION_TO_TECHNIQUES,
    MEDITATION_TECHNIQUES,
)

default_client = genai.Client(api_key=GEMINI_API_KEY)


def generate_prompt(
    journal_entry: str,
    emotion_scores: dict,
    duration_minutes: int,
    spiritual_path: str,
    meditation_type: str,
    mode: str = "tts",
) -> str:
    """
    Generates a Gemini-compatible prompt for a personalized meditation script.
    """
    emotion_summary = ", ".join(f"{k}: {v:.5f}" for k, v in emotion_scores.items())
    top_emotion = max(emotion_scores, key=emotion_scores.get)

    meditation_guidance = MEDITATION_TYPE_STYLES.get(
        meditation_type.lower(), MEDITATION_TYPE_STYLES["self-love"]
    )
    meditation_techniques = EMOTION_TO_TECHNIQUES.get(
        top_emotion.lower(), ["mindfulness"]
    )
    full_meditation_techniques = "\n".join(
        f"{tech}: {MEDITATION_TECHNIQUES.get(tech, MEDITATION_TECHNIQUES['mindfulness'])}"
        for tech in meditation_techniques
    )

    prompt = f"""
    You are an expert meditation guide, known for intuitive emotional insight, poetic metaphor,
    and the ability to craft deeply resonant meditations, spoken aloud.

    The user shared this reflection (their exact words):
    \"\"\"{journal_entry}\"\"\"

    Their analyzed emotional tone is:
    {emotion_summary}

    Preferences:
    - Duration: {duration_minutes} minutes
    - Spiritual perspective: {spiritual_path}
    - Meditation type: {meditation_type}

    Style guidance for this session:
    {meditation_guidance}

    Please utilize the following meditation technique(s) to guide the user:
    {full_meditation_techniques}

    When writing the guided meditation script, follow these **Do's**:

    • Explicitly reference and validate only what the user actually wrote.
    • Use second-person (“you”) throughout.
    • Create 1-3 vivid metaphors **directly** tied to their language.
    • Maintain a warm, compassionate, conversational tone.
    • Favor concise, rhythmic sentences, suitable for TTS.
    • Vary sentence length for natural flow.

    And observe these **Don'ts**:

    • Never invent or paraphrase experiences, emotions, or metaphors the user didn't state.
    • Do not fabricate imagery (e.g., “storm,” “drowning”) unless the user used those exact words.
    • Avoid clinical language, hedging (“if you'd like”), or abstract affirmations.
    • Do not use ellipses (`...`) or em-dashes (`—`); only commas or line breaks.
    • No scene headings, character names, dialogue, screenplay or story structure.

    Your task:
    """

    if mode == "dev":
        prompt += f"""
        1. Explain your reasoning about the user's emotional context.
        2. List the metaphors you chose and why.
        3. Write a ~{duration_minutes}-minute meditation script incorporating them.

        Format clearly with headings:
        **Reasoning on Emotional Context:**
        **Chosen Metaphors:**
        **{duration_minutes}-Minute Script:**
        """
    else:
        prompt += f"""
        Write a personalized guided meditation script (~{duration_minutes} minutes, ~{duration_minutes * 135} words),
        in a calm, poetic, emotionally grounded voice, ready for TTS playback.
        Begin immediately with a grounding cue, move into imagery, then close with re-entry to the present.
        """

    return prompt.strip()


def length_threshold(time: int, word_count: int, tolerance: float = 0.30) -> bool:
    """
    Returns True if `word_count` is within ±tolerance of (time * 135).
    """
    expected = time * 135
    lower = expected * (1 - tolerance)
    upper = expected * (1 + tolerance)
    return lower <= word_count <= upper


async def generate_meditation_script(
    prompt: str,
    time: int,
    tmp_root: str,
    client=None,
    max_loops: int = 10,
    max_total_retries: int = 3,
) -> str:
    """
    Generates a meditation script via Gemini. Writes the script as a .txt file under tmp_root.
    In production, uploads to GCS and deletes the local file. Returns either:
      - in dev (IS_PROD=False): the local path under tmp_root
      - in prod: the GCS URI of the uploaded script
    """
    if client is None:
        client = default_client

    # 1) Ensure tmp_root exists:
    os.makedirs(tmp_root, exist_ok=True)

    models = [
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-001",
    ]

    succeeded = False
    model_used = None

    # 2) Attempt up to max_total_retries
    for attempt in range(max_total_retries):
        # 2a) Try each model in turn
        for model_name in models:
            try:
                logger.info(
                    f"Attempt {attempt + 1}/{max_total_retries}: Trying model {model_name}"
                )
                chat = client.aio.chats.create(model=model_name)
                response = await chat.send_message(prompt)
                script = response.text
                model_used = model_name
                break
            except ServerError as e:
                # If 503, try next model
                if "503" in str(e):
                    logger.warning(
                        f"Model {model_name} overloaded (503). Trying next model..."
                    )
                    continue
                else:
                    raise
            except ClientError as e:
                # If rate-limited (429), back off
                if e.code == 429:
                    retry_delay = 30
                    try:
                        details = e.details["error"]["details"][2]
                        retry_delay = (
                            int(details.get("retryDelay", "30s").rstrip("s")) or 30
                        )
                    except Exception:
                        logger.warning("Could not parse retryDelay; using default 30s")
                    logger.warning(
                        f"Rate limit (429). Sleeping {retry_delay}s before retry..."
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise
        else:
            # No model succeeded this round
            logger.info("All models overloaded. Backing off before retry...")
            await asyncio.sleep(2**attempt)
            continue

        # 2b) Refinement loop: check word count and regenerate if needed
        loops = 0
        while loops < max_loops:
            word_count = len(script.split())
            if length_threshold(time, word_count):
                logger.info(
                    f"Script passed with {word_count} words after {loops}/{max_loops} refinement loops."
                )
                succeeded = True
                break

            logger.info(
                f"Script failed with {word_count} words after {loops + 1}/{max_loops} refinement loops. Regenerating..."
            )
            loops += 1
            await asyncio.sleep(2**attempt)
            try:
                chat = client.aio.chats.create(model=model_used)
                response = await chat.send_message(prompt)
                script = response.text
            except Exception as regen_error:
                logger.warning(f"Regeneration failed: {regen_error}")
                break

        if succeeded:
            break

    # 3) If we never succeeded, throw an error
    if not succeeded:
        logger.error(
            f"Exceeded maximum retries ({max_total_retries}). Meditation generation failed."
        )
        raise ValueError("threshold_unmet")

    # 4) Write the final script as a timestamped .txt under tmp_root
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    script_filename = f"script_{timestamp}.txt"
    script_output_path = os.path.join(tmp_root, script_filename)
    with open(script_output_path, "w") as f:
        f.write(script)

    logger.info(
        f"Script generated successfully after attempt {attempt + 1} using {model_used}"
    )

    # 5) If in prod, upload & delete; otherwise return local path
    if IS_PROD:
        gcs_uri = upload_to_gcs(local_path=script_output_path)
        logger.info(f"Script uploaded to GCS: {gcs_uri}")
        try:
            os.remove(script_output_path)
            logger.debug(f"Deleted local script: {script_output_path}")
        except Exception as e:
            logger.warning(
                f"Could not delete local script file {script_output_path}: {e}"
            )
        return gcs_uri

    return script_output_path
