import os
from google import genai
from params import TTS_DIR
from config.meditation_types import MEDITATION_TYPE_STYLES


def generate_prompt(
    journal_entry: str,
    emotion_scores: dict,
    time: int,
    spiritual_path: str,
    meditation_types: list,
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
        MEDITATION_TYPE_STYLES.get(mt.lower(), f"(No guidance for {mt})")
        for mt in meditation_types
    )

    prompt = f"""
    You are an expert meditation guide renowned for your intuitive emotional insight, poetic metaphor, and ability to craft meditations that resonate deeply when spoken aloud.

    Here is a user's journal entry:
    \"\"\"{journal_entry}\"\"\"

    Their analyzed emotional tone is:
    {emotion_summary}

    Preferences for this meditation:
    - Duration: {time} minutes
    - Meditation styles: {", ".join(meditation_types)}
    - Spiritual perspective: {spiritual_path}

    Refer to this meditation guidance for stylistic inspiration:
    {meditation_guidance}

    When writing the meditation script:
    - Explicitly reference and validate the user's personal experiences and emotions (e.g., anxiety from a work presentation, regret after a conflict). Clearly acknowledge these events before gently abstracting them.
    - Create 1-3 vivid, meaningful metaphors or symbolic scenarios closely linked to their experience (e.g., anxiety as "standing exposed in a silent storm").
    - Ensure metaphors organically emerge from the user's described experiences rather than feeling forced or generic.
    - Maintain a warm, compassionate, conversational tone, as though speaking directly to the user in a moment of personal guidance.
    - Favor concise, rhythmic sentences suitable for spoken delivery. Vary sentence length occasionally for a natural, engaging flow.
    - Avoid repetitive sentence structures, clinical language, hedging phrases (like "if you'd like" or "if that feels comfortable"), or overly abstract affirmations. Instead, employ gentle yet confident invitations (e.g., "imagine," "notice," "perhaps").
    - Do **not** use ellipses (`...`), emdashes (`—`) since they often cause unnatural stutters in voice playback. Only use line breaks or commas (`,`) for soft pacing instead.
    - The final output should feel completely personalized to the user.

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
        Write a complete meditation script (~{time} minutes) using your chosen metaphors.

        Maintain a calm, poetic voice consistent with the {spiritual_path} tradition.

        Return only the meditation script, without any titles, labels, explanations, or formatting instructions. Your output will be used directly for text-to-speech playback.
        """

    return prompt.strip()


def length_threshold(time: int, word_count: int, tolerance: float = 0.10) -> bool:
    """
    Returns True if word_count is within ±tolerance of expected words for the given time.
    """
    expected = time * 135
    lower = expected * (1 - tolerance)
    upper = expected * (1 + tolerance)
    return lower <= word_count <= upper


async def generate_meditation_script(
    prompt: str,
    time: int,
    gemini_key: str,
    max_loops: int = 10,
) -> str:
    """
    Asynchronously generates a meditation script using the Gemini API,
    and iteratively refines it until it matches the desired duration (via word count).

    Parameters:
        prompt (str): The initial meditation prompt.
        time (int): Desired duration in minutes.
        gemini_key (str): Your Gemini API key.
        max_loops (int): Max attempts before failing out.

    Returns:
        str: Final meditation script matching duration.
    """
    expected_length = time * 135  # ~135 words per minute
    client = genai.Client(api_key=gemini_key)
    chat = client.aio.chats.create(model="models/gemini-2.0-flash")

    response = await chat.send_message(prompt)
    script = response.text
    loops = 0

    while not length_threshold(time, len(script.split())):
        loops += 1
        if loops >= max_loops:
            raise RuntimeError(
                f"Exceeded max refinement attempts ({max_loops}) without reaching word count goal "
                f"for {time}-minute meditation. Last output was {len(script.split())} words."
            )

        feedback = (
            f"The script is currently {len(script.split())} words long, which doesn't match a "
            f"{time}-minute meditation. Please revise it to approximately {expected_length} words, "
            "while keeping the same emotional tone, pacing, and structure."
        )

        response = await chat.send_message(feedback)
        script = response.text

    with open(os.path.join(TTS_DIR, "script.txt"), "w") as f:
        f.write(script)

    return script
