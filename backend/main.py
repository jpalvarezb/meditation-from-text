import asyncio
from app.emotion_scoring import emotion_classification
from app.script_generator import generate_prompt, generate_meditation_script
from app.tts_generator import generate_tts, align_audio_text
from app.sound_engineer import sound_engineer_pipeline
from config.params import GEMINI_API_KEY


async def main():
    # --- Step 0: User inputs (mocked for now) ---
    journal_entry = (
        "Today I felt overwhelmed by meetings but also hopeful for the future."
    )
    meditation_types = ["mindfulness", "visualization"]
    spiritual_path = "Buddhist"
    duration_minutes = 3

    print("✅ Starting full meditation generation...")

    # --- Step 1: Analyze emotions ---
    print("🔍 Scoring emotions...")
    emotion_summary = emotion_classification(journal_entry)
    print(f"Emotion scores: {emotion_summary}")

    # --- Step 2: Generate meditation prompt ---
    print("📝 Building meditation prompt...")
    prompt = generate_prompt(
        journal_entry=journal_entry,
        emotion_scores=emotion_summary,
        time=duration_minutes,
        spiritual_path=spiritual_path,
        meditation_types=meditation_types,
        mode="tts",
    )

    # --- Step 3: Generate meditation script and save it ---
    print("🎙️ Generating meditation script...")
    script_path = await generate_meditation_script(
        prompt=prompt,
        time=duration_minutes,
        gemini_key=GEMINI_API_KEY,
    )

    # --- Step 4: Load the saved script ---
    with open(script_path, "r") as f:
        script_text = f.read()

    import ipdb

    ipdb.set_trace()

    # --- Step 5: Generate TTS from script ---
    print("🔊 Generating TTS audio...")
    tts_path = generate_tts(script_text)

    # --- Step 6: Align TTS audio with script text ---
    print("🧭 Aligning audio and text...")
    alignment_path = tts_path.replace(".wav", ".json")
    align_audio_text(
        audio_path=tts_path,
        text_path=script_path,
        output_json_path=alignment_path,
    )

    # --- Step 7: Sound Engineer final meditation mix ---
    print("🎼 Sound engineering final meditation...")
    output_filename = "final_meditation_mix.wav"

    final_mix_path = sound_engineer_pipeline(
        tts_path=tts_path,
        alignment_json_path=alignment_path,
        emotion_summary=emotion_summary,
        output_filename=output_filename,
    )

    print("✅ Meditation generation complete!")
    print(f"Final meditation saved at: {final_mix_path}")


if __name__ == "__main__":
    asyncio.run(main())
