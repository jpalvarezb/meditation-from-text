from datetime import datetime
from app.logger import logger
from app.emotion_scoring import emotion_classification
from app.script_generator import generate_prompt, generate_meditation_script
from app.tts_generator import generate_tts, align_audio_text
from app.sound_engineer import sound_engineer_pipeline
from app.cloud_utils import (
    resolve_asset,
    generate_signed_url,
    clean_up_tmp_folder,
)


# The main function exposed to API
async def meditation_engine(
    journal_entry: str,
    duration_minutes: int,
    meditation_type: str,
    mode: str = "tts",
    tmp_root: str = "/tmp",
) -> dict:
    logger.info(
        f"Received inputs - duration: {duration_minutes} min, type: {meditation_type}, mode: {mode}"
    )
    logger.debug(f"Journal entry: {journal_entry}")
    try:
        logger.info("Scoring emotions...")
        emotion_summary = emotion_classification(journal_entry)
        logger.info(f"Emotion summary: {emotion_summary}")

        logger.info("Building meditation prompt...")
        prompt = generate_prompt(
            journal_entry=journal_entry,
            emotion_scores=emotion_summary,
            duration_minutes=duration_minutes,
            spiritual_path="Buddhist",  # TODO: Need more audio assets for other paths
            meditation_type=meditation_type,
            mode=mode,
        )
        logger.debug(f"Prompt: {prompt}")

        try:
            logger.info("Generating meditation script...")
            script_path = await generate_meditation_script(
                prompt=prompt, time=duration_minutes, tmp_root=tmp_root
            )
            logger.info(f"Script saved at: {script_path}")
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            raise

        script_local = resolve_asset(script_path)

        logger.info("Generating TTS audio...")
        tts_path = generate_tts(script_local, tmp_root=tmp_root)
        logger.info(f"TTS audio saved at: {tts_path}")

        tts_local = resolve_asset(tts_path, tmp_root)

        logger.info("Aligning audio and text...")
        alignment_path = align_audio_text(tts_local, script_local, tmp_root=tmp_root)
        logger.info(f"Alignment JSON saved at: {alignment_path}")

        logger.info("Sound engineering final meditation...")
        output_filename = f"final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        final_mix_path = sound_engineer_pipeline(
            tts_path=tts_path,
            alignment_json_path=alignment_path,
            emotion_summary=emotion_summary,
            output_filename=output_filename,
            tmp_root=tmp_root,
        )
        final_signed_url = None
        if final_mix_path.startswith("gs://"):
            final_signed_url = generate_signed_url(final_mix_path)
            logger.info(f"Final mix saved at: {final_mix_path}")
        logger.info("Medition generation pipeline finished successfully.")
        # Clean Up local files
        clean_up_tmp_folder(tmp_root)
        return {
            "final_signed_url": final_signed_url
            if final_signed_url
            else "Development mode",
            # If not in production, return local path
            "final_audio_path": final_mix_path,
            "emotion_summary": emotion_summary,
            "script_path": script_path,
            "tts_path": tts_path,
            "alignment_path": alignment_path,
        }

    except Exception as e:
        logger.error(f"Error generating meditation: {e}", exc_info=True)
        raise
