import os
import asyncio
from google import genai
from datetime import datetime
from app.logger import logger
from config.params import GEMINI_API_KEY, TTS_DIR
from google.genai.errors import ServerError, ClientError
from config.meditation_types import MEDITATION_TYPE_STYLES

client = genai.Client(api_key=GEMINI_API_KEY)


def generate_prompt(
    journal_entry: str,
    emotion_scores: dict,
    time: int,
    spiritual_path: str,
    meditation_type: str,
    mode: str = "tts",
) -> str:
    """
    Generates a Gemini-compatible prompt for a personalized meditation script.

    Parameters:
        journal_entry (str): User's journal reflection.
        emotion_scores (dict): Dictionary of emotion: score pairs.
        time (int): Desired duration of meditation in minutes.
        spiritual_path (str): Spiritual/philosophical tone (e.g., "Buddhist", "Christian").
        meditation_types (list): One or more meditation styles (e.g., ["mindfulness", "visualization"]).
        mode (str): "tts" for output-ready script or "dev" for full reasoning output.

    Returns:
        str: Prompt string to send to Gemini.
    """
    emotion_summary = ", ".join(f"{k}: {v:.5f}" for k, v in emotion_scores.items())

    meditation_guidance = "\n".join(
        MEDITATION_TYPE_STYLES.get(mt.lower(), "default") for mt in meditation_type
    )

    prompt = f"""
    You are an expert meditation guide renowned for your intuitive emotional insight, poetic metaphor, and ability to craft meditations that resonate deeply when spoken aloud.
    As the meditation instructor, you are trained in the following core techniques. You may apply one or combine several depending on the user\'s emotional profile and needs:
	Mindfulness: Guide the listener through gentle, non-judgmental awareness of breath, body, and present-moment sensations. Use a calm, observational tone. Encourage acceptance of thoughts and feelings exactly as they are.
	Visualization: Use vivid, symbolic imagery to guide the listener through a metaphorical landscape that mirrors their emotional state. Let the imagery unfold organically, supporting transformation through metaphor.
	Breathing: Center the meditation on the breath. Offer slow, structured breathing cues (e.g., box breathing, deep belly breaths). Keep language rhythmic and minimal, syncing with the natural cadence of breath.
	Affirmations: Repeat supportive, emotionally attuned affirmations. Promote self-love, resilience, and inner strength. Keep phrasing simple, intentional, and calming.

    You are writing this meditation for someone who shared the following personal reflection:
    \"\"\"{journal_entry}\"\"\"

    This is their actual, lived experience. Speak to them directly, using second person ("you") throughout the script.
    Never reinterpret, generalize, or paraphrase what they wrote. Stay anchored to their exact words.

    Their analyzed emotional tone is:
    {emotion_summary}

    Preferences for this meditation:
    - Duration: {time} minutes
    - Meditation styles: {", ".join(meditation_type)}
    - Spiritual perspective: {spiritual_path}

    Refer to this meditation guidance for stylistic inspiration:
    {meditation_guidance}

    When writing the guided meditation script:
    - Explicitly reference and validate the user's personal experiences and emotions. Use only details that are directly mentioned or clearly implied by the user's shared experience.
    - Do **not** fabricate or reference feelings, metaphors, or events not stated in the shared experience. If uncertain, ask or gently reflect using the user's actual words.
    - Create 1-3 vivid, meaningful metaphors or symbolic scenarios closely linked to their experience (e.g., anxiety as "standing exposed in a silent storm").
    - Ensure metaphors organically emerge from the user's described experiences rather than feeling forced or generic.
    - Maintain a warm, compassionate, conversational tone, as though speaking directly to the user in a moment of personal guidance.
    - Favor concise, rhythmic sentences suitable for spoken delivery. Vary sentence length occasionally for a natural, engaging flow.
    - Avoid repetitive sentence structures, clinical language, hedging phrases (like "if you'd like" or "if that feels comfortable"), or overly abstract affirmations. Instead, employ gentle yet confident invitations (e.g., "imagine," "notice," "perhaps").
    - Do **not** use ellipses (`...`), emdashes (`—`) since they often cause unnatural stutters in voice playback. Only use line breaks or commas (`,`) for soft pacing instead.
    - This meditation will be used in a real mindfulness app. The listener is expecting a direct, emotionally attuned meditation — not fiction, dialogue, or theatrical storytelling.
    - The final output should feel completely personalized to the user.

    ⚠️ Anchoring Rule:
    Do not invent or reinterpret events, emotions, or metaphors. All emotional references and imagery must be directly grounded in the user's original words.
    Use only what they actually wrote, in their exact phrasing.

    ⚠️ Do not reference or invent emotional metaphors (e.g., “storm,” “drowning,” “intense feelings”) unless the user used these terms directly in their journal entry.

    ✅ You must base all emotional references, symbols, or metaphors explicitly on their **own language**.

    ✳️ If a user mentions feeling “hopeful,” “overwhelmed by meetings,” or “anxious after a presentation,” you must use those exact phrases and emotions when validating their experience.

    ⛔ Do not paraphrase the journal entry or reinterpret it. Never reference feelings, scenarios, or symbols the user did not mention.

    Your task:
    """

    if mode == "dev":
        prompt += f"""
        1. Clearly explain your reasoning about the user's emotional context.
        2. List the symbolic metaphors you chose and explain why they are relevant.
        3. Write a guided meditation script (~{time} minutes) using these metaphors.

        Structure your response clearly:
        **Reasoning on Emotional Context:**
        **Symbolic Metaphors:**
        **{time}-Minute Meditation Guide Script:**
        """
    else:
        prompt += f"""
        Your task is to write a personalized **guided meditation** script (approximately {time} minutes, ~{time * 135} words). The tone should remain calm, poetic, and emotionally grounded.

        ⚠️ Do not write a story, dialogue, play, screenplay, or film scene.

        The user will hear this script via a voice narrator — your language should be reflective, direct, and suited for TTS playback.

        ✳️ Structure:
        - Begin with a short grounding or breath cue.
        - Move into emotionally resonant imagery or metaphor derived from the journal entry and emotion summary.
        - Guide the listener gently into awareness, reflection, or visualization.
        - Close with a clear, peaceful re-entry to the present.

        ✳️ Constraints:
        - No scene headings, character names, or dramatized dialogue.
        - Avoid formatting marks (titles, asterisks, headings).
        - Avoid phrases like "Here's your script" or "Scene start", "Here's your meditation" or "Okay, here's a revised version".
        - Do not explain your choices. Output only the **spoken meditation script**.
        - Your task is to write a direct **guided meditation** script for a real mindfulness app. The script should be approximately {time} minutes long (~{time * 135} words).
        - Do **not** explain what you're doing.
        - Do **not** respond as if editing or summarizing anything. You are the voice of the meditation guide.

        ✅ Only output the meditation script itself, written in second-person, meant to be read aloud with a calming tone.

        Begin immediately with the meditation.

        End your meditation script naturally, as a meditative guide would.
        """

    return prompt.strip()


def length_threshold(time: int, word_count: int, tolerance: float = 0.10) -> bool:
    expected = time * 135
    lower = expected * (1 - tolerance)
    upper = expected * (1 + tolerance)
    return lower <= word_count <= upper


async def generate_meditation_script(
    prompt: str,
    time: int,
    client=client,  # <-- CHANGE: pass the Gemini client directly
    max_loops: int = 10,
    max_total_retries: int = 3,
) -> str:
    """
    Fully robust meditation script generator with:
    - Model fallback if overloaded
    - Retry full generation if feedback refinement fails
    - Exponential backoff between retries
    """
    expected_length = time * 135

    models = [
        "models/gemini-2.0-flash",
        "models/gemini-2.0-flash-001",
        "models/gemini-2.0-flash-002",
    ]

    model_used = None  # track the currently used model

    for attempt in range(max_total_retries):
        for model_name in models:
            try:
                logger.info(
                    f"Attempt {attempt + 1}/{max_total_retries}: Trying model {model_name}"
                )
                chat = client.aio.chats.create(model=model_name)
                response = await chat.send_message(prompt)
                script = response.text
                model_used = model_name
                break  # successful, break model loop
            except ServerError as e:
                if "503" in str(e):
                    logger.warning(
                        f"Model {model_name} overloaded (503). Trying next model..."
                    )
                    continue
                else:
                    raise e
            except ClientError as e:
                if e.code == 429:
                    retry_delay = 30  # fallback default
                    try:
                        details = e.details["error"]["details"][2]
                        if isinstance(details, dict):
                            retry_str = details.get("retryDelay", "30s")
                            retry_delay = int(retry_str.replace("s", ""))
                            if retry_delay == 0:
                                retry_delay = 30
                    except Exception as parse_error:
                        logger.warning(f"Failed to parse retryDelay: {parse_error}")

                    logger.warning(
                        f"Rate limit hit (429). Sleeping {retry_delay}s before retry..."
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise e
        else:
            logger.info(
                "All models overloaded. Retrying full generation after backoff..."
            )
            await asyncio.sleep(2**attempt)
            continue

        # ✅ Initial generation successful, refine script
        loops = 0
        fallback_models = models[
            models.index(model_used) :
        ]  # start from current model down
        model_index = 0

        while not length_threshold(time, len(script.split())):
            loops += 1
            if loops >= max_loops:
                logger.info(
                    f"Max refinement loops reached {loops}/{max_loops}. Restarting full generation..."
                )
                await asyncio.sleep(2**attempt)
                break

            feedback = feedback = (
                f"The current meditation script is {len(script.split())} words long. "
                f"The target length is approximately {expected_length} words (±15). "
                "Regenerate the full script to meet this length, but preserve all personalization, especially direct references to the user's experience that they shared and emotional context."
                "Do not summarize or reinterpret the user's experience that they shared. Reference their exact words when validating emotions or crafting metaphors."
                "Maintain vivid, emotionally grounded metaphors and specific acknowledgments of the user's feelings and experience. "
                "Keep the tone poetic, calming, and suitable for spoken delivery. "
                "Output only the meditation script — no headers, explanations, or formatting."
            )

            try:
                chat = client.aio.chats.create(model=fallback_models[model_index])
                response = await chat.send_message(feedback)
                script = response.text
            except ServerError as e:
                if "503" in str(e):
                    logger.warning(
                        f"Model {fallback_models[model_index]} overloaded during refinement (503). Trying next fallback model:{fallback_models[model_index + 1]} ..."
                    )
                    model_index += 1
                    if model_index >= len(fallback_models):
                        logger.warning(
                            "No more fallback models during refinement. Restarting full generation..."
                        )
                        await asyncio.sleep(2**attempt)
                        break
                    await asyncio.sleep(2**attempt)
                    continue
                else:
                    raise e
            except ClientError as e:
                if e.code == 429:
                    retry_delay = 30
                    try:
                        details = e.details["error"]["details"][2]
                        if isinstance(details, dict):
                            retry_str = details.get("retryDelay", "30s")
                            retry_delay = int(retry_str.replace("s", ""))
                    except Exception as parse_error:
                        logger.warning(f"Failed to parse retryDelay: {parse_error}")

                    logger.warning(
                        f"Rifenement loop {loops}/{max_loops} failed: Rate limit hit (429). Sleeping {retry_delay}s before retry..."
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise e
        else:
            break  # ✅ Refinement successful

    else:
        logger.error(
            f"Exceeded maximum retries {attempt + 1}/{max_total_retries}. Meditation generation failed."
        )
        raise RuntimeError

    # Save script
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_filename = f"script_{timestamp}.txt"
    script_output_path = os.path.join(TTS_DIR, script_filename)

    with open(script_output_path, "w") as f:
        f.write(script)

    logger.info(
        f"Meditation script generated successfully after {attempt + 1} attempt(s) using {model_used}"
    )
    return script_output_path
