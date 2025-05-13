import os
import asyncio
from google import genai
from datetime import datetime
from app.logger import logger
from config.params import GEMINI_API_KEY, TTS_DIR
from google.genai.errors import ServerError, ClientError
from config.meditation_types import MEDITATION_TYPE_STYLES
from config.emotion_techniques import EMOTION_TO_TECHNIQUES, MEDITATION_TECHNIQUES

client = genai.Client(api_key=GEMINI_API_KEY)


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
    # 1) Summarize emotions
    emotion_summary = ", ".join(f"{k}: {v:.5f}" for k, v in emotion_scores.items())
    top_emotion = max(emotion_scores, key=emotion_scores.get)

    # 2) Pull in the style guidance, falling back to "self-love"
    meditation_guidance = MEDITATION_TYPE_STYLES.get(
        meditation_type.lower(), MEDITATION_TYPE_STYLES["self-love"]
    )

    # 2a) Pull the techniques to be used in the meditation
    meditation_techniques = EMOTION_TO_TECHNIQUES.get(
        top_emotion.lower(), ["mindfulness"]
    )

    full_meditation_techniques = "\n".join(
        f"{tech}: {MEDITATION_TECHNIQUES.get(tech, MEDITATION_TECHNIQUES['mindfulness'])}"
        for tech in meditation_techniques
    )

    # 3) Build the prompt
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
    expected = time * 135
    lower = expected * (1 - tolerance)
    upper = expected * (1 + tolerance)
    return lower <= word_count <= upper


async def generate_meditation_script(
    prompt: str,
    time: int,
    client=client,
    max_loops: int = 10,
    max_total_retries: int = 3,
) -> str:
    """
    Fully robust meditation script generator with:
    - Model fallback if overloaded
    - Retry full generation if feedback refinement fails
    - Exponential backoff between retries
    """
    models = [
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-001",
        "models/gemini-2.0-flash-002",
    ]

    succeeded = False
    model_used = None

    for attempt in range(max_total_retries):
        # --- Initial generation with model fallback ---
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
                if "503" in str(e):
                    logger.warning(
                        f"Model {model_name} overloaded (503). Trying next model..."
                    )
                    continue
                else:
                    raise
            except ClientError as e:
                if e.code == 429:
                    # exponential backoff / respect retryDelay
                    retry_delay = 30
                    try:
                        details = e.details["error"]["details"][2]
                        retry_delay = (
                            int(details.get("retryDelay", "30s").rstrip("s")) or 30
                        )
                    except (KeyError, IndexError, TypeError, ValueError) as parse_error:
                        logger.warning(
                            f"Could not parse retryDelay, using default: {parse_error}"
                        )
                    logger.warning(
                        f"Rate limit (429). Sleeping {retry_delay}s before retry..."
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise
        else:
            # no model succeeded, back off and retry
            logger.info("All models overloaded. Backing off before retry...")
            await asyncio.sleep(2**attempt)
            continue

        # --- Refinement loop to adjust length ---
        loops = 0
        while loops < max_loops:
            word_count = len(script.split())
            if length_threshold(time, word_count):
                logger.info(
                    f"Script passed {word_count} words threshold check after {loops}/{max_loops} refinement loops."
                )
                succeeded = True
                break

            logger.info(
                f"Script failed {word_count} words threshold check after {loops + 1}/{max_loops} refinement loops. Restarting full generation..."
            )
            loops += 1
            await asyncio.sleep(2**attempt)
            try:
                # Re-run generation
                chat = client.aio.chats.create(model=model_used)
                response = await chat.send_message(prompt)
                script = response.text
            except Exception as regen_error:
                logger.warning(f"Regeneration failed: {regen_error}")
                break

        # if we hit the length target, break out of retry loop
        if succeeded:
            break

    # after retries, if still not succeeded, error out
    if not succeeded:
        logger.error(
            f"Exceeded maximum retries ({max_total_retries}). Meditation generation failed."
        )
        raise RuntimeError("Meditation generation failed.")

    # Save the final script
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_filename = f"script_{timestamp}.txt"
    script_output_path = os.path.join(TTS_DIR, script_filename)
    with open(script_output_path, "w") as f:
        f.write(script)
    logger.info(
        f"Script generated successfully after attempt {attempt + 1} using {model_used}"
    )

    return script_output_path
