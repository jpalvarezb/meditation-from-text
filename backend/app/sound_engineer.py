import os
import json
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
from app.decision_maker import choose_assets
from config.trigger_words import TRIGGER_WORDS
from app.audio_utils import (
    soften_voice,
    build_seamless_loop,
    build_intro_layer,
    normalize_volume,
    detect_chime_tail,
    next_bar_chime,
    extract_word_timings_from_fragments,
    build_outro_segment,
)
from config.params import SOUNDSCAPES_DIR, TONES_DIR, CHIMES_DIR, OUTPUT_DIR


def sound_engineer_pipeline(
    tts_path: str,
    alignment_json_path: str,
    emotion_summary: dict,
    output_filename: str = "final_mix.wav",
) -> str:
    """Main pipeline for creating a meditation soundscape."""

    # 1) Choose assets
    chosen = choose_assets(emotion_summary)
    amb_p = os.path.join(SOUNDSCAPES_DIR, chosen["ambient"])
    tone_p = os.path.join(TONES_DIR, chosen["tone"])
    start_file = chosen.get("start_chime", "start_chime_gong.wav")
    end_file = chosen.get("end_chime", "end_chime_singing_bowl_1.wav")
    start_p = os.path.join(CHIMES_DIR, start_file)
    end_p = os.path.join(CHIMES_DIR, end_file)

    amb_vol = chosen.get("ambient_volume_dBFS", -32.0)
    tone_vol = chosen.get("tone_volume_dBFS", -36.0)

    # 2) Load & soften TTS
    raw_tts = AudioSegment.from_file(tts_path)
    softened = soften_voice(raw_tts)

    # 3) Read alignment
    with open(alignment_json_path) as f:
        fragments = json.load(f)["fragments"]

    # 4) Load start chime and detect offset
    start_chime = AudioSegment.from_file(start_p)[:32_000]
    tts_offset = detect_chime_tail(start_chime)

    # 5) Load ambient and tone
    ambient = normalize_volume(AudioSegment.from_file(amb_p), target_dBFS=amb_vol)
    tone = normalize_volume(AudioSegment.from_file(tone_p), target_dBFS=tone_vol)

    # 6) Build intro under chime
    fade_ms = len(start_chime)
    amb_intro = build_intro_layer(ambient, fade_ms).fade_in(fade_ms)
    tone_intro = build_intro_layer(tone, fade_ms).fade_in(fade_ms)
    intro_mix = start_chime.overlay(amb_intro).overlay(tone_intro)

    # 7) Prepare loopable background
    amb_rest = ambient[fade_ms:] or ambient
    tone_rest = tone[fade_ms:] or tone
    bg_loop = amb_rest.overlay(tone_rest, loop=True)

    # 8) Build complete TTS track
    tts_full = AudioSegment.silent(duration=tts_offset) + softened
    tts_len = len(tts_full)

    # 9) Build background
    total_needed = tts_len
    rest_needed = max(total_needed - len(intro_mix), 0)
    repeats = (rest_needed // len(bg_loop)) + 1
    looped_bg = build_seamless_loop(bg_loop, repeats)
    full_background = intro_mix + looped_bg[:rest_needed]

    if len(full_background) < total_needed:
        full_background += AudioSegment.silent(
            duration=(total_needed - len(full_background))
        )

    # 10) Mix TTS onto background
    base_mix = full_background.overlay(tts_full, position=0)

    # 11) Insert trigger chimes
    word_times = extract_word_timings_from_fragments(fragments, offset_ms=tts_offset)
    for word, ms in word_times:
        if word.lower().strip(".,!?") in TRIGGER_WORDS:
            ch = normalize_volume(next_bar_chime(), target_dBFS=-40.0)
            base_mix = base_mix.overlay(ch, position=ms)

    # 12) Build outro segment
    end_chime = AudioSegment.from_file(end_p)
    outro_segment = build_outro_segment(end_chime, full_background)

    # 13) Find actual TTS end
    tts_non_silent = detect_nonsilent(
        base_mix, min_silence_len=100, silence_thresh=base_mix.dBFS - 16
    )
    if tts_non_silent:
        last_spoken_end = tts_non_silent[-1][1]
    else:
        last_spoken_end = tts_len

    # 14) Stitch final mix: base_mix up to end of TTS, then outro directly
    final_mix = base_mix[:last_spoken_end] + outro_segment

    # 15) Export
    out_path = os.path.join(OUTPUT_DIR, output_filename)
    final_mix.export(out_path, format="wav")

    return out_path
