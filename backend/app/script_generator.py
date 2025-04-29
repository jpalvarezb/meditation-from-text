import os
import asyncio
from google import genai
from datetime import datetime
from config.params import TTS_DIR
from google.genai.errors import ServerError, ClientError
from config.meditation_types import MEDITATION_TYPE_STYLES

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


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

    models = ["models/gemini-2.0-flash", "models/gemini-1.5-flash"]

    for attempt in range(max_total_retries):
        for model_name in models:
            try:
                print(f"🔹 Attempt {attempt + 1}: Trying model {model_name}")
                chat = client.aio.chats.create(model=model_name)
                response = await chat.send_message(prompt)
                script = response.text
                model_used = model_name
                break  # successful, break model loop
            except ServerError as e:
                if "503" in str(e):
                    print(
                        f"⚡ Model {model_name} overloaded (503). Trying next model..."
                    )
                    continue
                else:
                    raise e
            except ClientError as e:
                import ipdb

                ipdb.set_trace()
                if e.status_code == 429:
                    retry_delay = 30  # fallback default
                    try:
                        details = e.args[0]
                        if "retryDelay" in details:
                            import re

                            m = re.search(r"'retryDelay': '(\d+)s'", details)
                            if m:
                                retry_delay = int(m.group(1))
                    except Exception:
                        pass

                    print(
                        f"⚡ Rate limit hit (429). Waiting {retry_delay}s before retry..."
                    )
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    raise e
        else:
            print("🔄 All models overloaded. Retrying full generation after backoff...")
            await asyncio.sleep(2**attempt)
            continue

        # ✅ Initial generation successful, refine script
        loops = 0
        while not length_threshold(time, len(script.split())):
            loops += 1
            if loops >= max_loops:
                print("⚡ Max refinement loops reached. Restarting full generation...")
                await asyncio.sleep(2**attempt)
                break

            feedback = (
                f"The script is currently {len(script.split())} words long. "
                f"Please revise it to approximately {expected_length} words."
            )

            try:
                chat = client.aio.chats.create(model=model_used)
                response = await chat.send_message(feedback)
                script = response.text
            except ServerError as e:
                if "503" in str(e):
                    print(
                        f"⚡ Model {model_used} overloaded during feedback. Restarting full generation..."
                    )
                    await asyncio.sleep(2**attempt)
                    break
                else:
                    raise e
        else:
            break  # ✅ Refinement successful

    else:
        raise RuntimeError("❌ Exceeded maximum retries. Meditation generation failed.")

    # Save script
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_filename = f"script_{timestamp}.txt"
    script_output_path = os.path.join(TTS_DIR, script_filename)

    with open(script_output_path, "w") as f:
        f.write(script)

    print(
        f"✅ Meditation script generated successfully after {attempt + 1} attempt(s) using {model_used}"
    )
    return script_output_path
