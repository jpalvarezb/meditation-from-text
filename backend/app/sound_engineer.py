import os
import json
from pydub import AudioSegment
from decision_maker import choose_assets
from config.trigger_words import TRIGGER_WORDS
from audio_utils import (
    soften_voice,
    build_seamless_loop,
    build_intro_layer,
    normalize_volume,
    detect_chime_tail,
    next_bar_chime,
    extract_word_timings_from_fragments,
    build_outro_segment,
)
from params import SOUNDSCAPES_DIR, TONES_DIR, CHIMES_DIR, OUTPUT_DIR


def sound_engineer_pipeline(
    tts_path: str,
    alignment_json_path: str,
    emotion_summary: dict,
    output_filename: str = "final_mix.wav",
) -> str:
    # Choose assets based on emotion
    chosen = choose_assets(emotion_summary)

    ambient_path = os.path.join(SOUNDSCAPES_DIR, chosen["ambient"])
    tone_path = os.path.join(TONES_DIR, chosen["tone"])
    start_chime_file = chosen.get("start_chime", "start_chime_gong.wav")
    end_chime_file = chosen.get("end_chime", "end_chime_singing_bowl_1.wav")

    start_chime_path = os.path.join(CHIMES_DIR, start_chime_file)
    end_chime_path = os.path.join(CHIMES_DIR, end_chime_file)

    ambient_volume_dBFS = chosen.get("ambient_volume_dBFS", -32.0)
    tone_volume_dBFS = chosen.get("tone_volume_dBFS", -36.0)

    # Load and soften TTS
    raw_tts = AudioSegment.from_file(tts_path)
    softened = soften_voice(raw_tts)

    # Load alignment
    with open(alignment_json_path) as f:
        fragments = json.load(f)["fragments"]

    # Load and preserve full start chime
    start_chime = AudioSegment.from_file(start_chime_path)
    start_chime = start_chime[:32000]  # cap start chime at 32 seconds
    tts_start_offset = detect_chime_tail(start_chime)

    # Background layers
    fade_duration = len(start_chime)
    ambient = normalize_volume(
        AudioSegment.from_file(ambient_path), target_dBFS=ambient_volume_dBFS
    )
    tone = normalize_volume(
        AudioSegment.from_file(tone_path), target_dBFS=tone_volume_dBFS
    )

    ambient_intro = build_intro_layer(ambient, fade_duration).fade_in(fade_duration)
    tone_intro = build_intro_layer(tone, fade_duration).fade_in(fade_duration)
    intro_with_chime = start_chime.overlay(ambient_intro).overlay(tone_intro)

    # Prepare ambient and tone for looping
    ambient_rest = ambient[fade_duration:]
    tone_rest = tone[fade_duration:]

    # Handle edge case: ambient too short after intro
    if len(ambient_rest) == 0:
        ambient_rest = ambient
    if len(tone_rest) == 0:
        tone_rest = tone

    background_loop = ambient_rest.overlay(tone_rest, loop=True)

    # Build full TTS: softened voice + silence offset
    tts = AudioSegment.silent(duration=tts_start_offset) + softened
    tts_duration = len(tts)
    print(f"TTS duration: {tts_duration / 1000:.2f}s")

    # End chime
    end_chime = AudioSegment.from_file(end_chime_path)

    buffer_before_chime = 2000  # 2 seconds
    chime_duration = len(end_chime)
    total_duration_needed = tts_duration + buffer_before_chime + chime_duration

    # Build full background
    bg_needed = max(total_duration_needed - len(intro_with_chime), 0)
    loop_repeats = (bg_needed // len(background_loop)) + 1
    looped_bg = build_seamless_loop(background_loop, loop_repeats)
    full_background = intro_with_chime + looped_bg[:bg_needed]

    if len(full_background) < total_duration_needed:
        full_background += AudioSegment.silent(
            duration=(total_duration_needed - len(full_background))
        )

    # Mix TTS into background
    base_mix = full_background.overlay(tts)

    # Chime timing from alignment
    word_timings = extract_word_timings_from_fragments(
        fragments, offset_ms=tts_start_offset
    )

    for word, end_ms in word_timings:
        clean_word = word.lower().strip(".,!?")
        if clean_word in TRIGGER_WORDS:
            chime_audio = normalize_volume(next_bar_chime(), target_dBFS=-40.0)
            base_mix = base_mix.overlay(chime_audio, position=end_ms)

    # Build outro segment
    outro_segment = build_outro_segment(end_chime, background_loop)

    # Final mix = base mix + outro
    final_mix = base_mix.overlay(outro_segment, position=tts_duration)

    # Export
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    final_mix.export(output_path, format="wav")

    print(f"Final mix saved to: {output_path}")
    print(f"Final duration: {len(final_mix) / 1000:.2f} seconds")

    return output_path
