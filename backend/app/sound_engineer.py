import os
import json
import math
import numpy as np
from pydub import AudioSegment
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
    """
    Simpler pipeline: build one long background, fade its tail, then overlay TTS and chime.
    """

    # 1) Choose assets & load files
    chosen = choose_assets(emotion_summary)
    amb = normalize_volume(
        AudioSegment.from_file(os.path.join(SOUNDSCAPES_DIR, chosen["ambient"])),
        target_dBFS=chosen.get("ambient_volume_dBFS", -32.0),
    )
    tone = normalize_volume(
        AudioSegment.from_file(os.path.join(TONES_DIR, chosen["tone"])),
        target_dBFS=chosen.get("tone_volume_dBFS", -36.0),
    )
    start_chime = AudioSegment.from_file(
        os.path.join(
            CHIMES_DIR, chosen.get("start_chime", "start_chime_paiste_gong.wav")
        )
    )
    end_chime = AudioSegment.from_file(
        os.path.join(CHIMES_DIR, chosen.get("end_chime", "end_chime_singing_bowl.wav"))
    )

    # 2) Build intro
    fade_ms = len(start_chime)
    amb_intro = build_intro_layer(amb, fade_ms).fade_in(fade_ms)
    tone_intro = build_intro_layer(tone, fade_ms).fade_in(fade_ms)
    intro_mix = start_chime.overlay(amb_intro).overlay(tone_intro)

    # 3) Make one seamless loop for the rest
    amb_rest = amb[fade_ms:] or amb
    tone_rest = tone[fade_ms:] or tone
    bg_loop = amb_rest.overlay(tone_rest, loop=True)

    # 4) Load & soften TTS
    raw_tts = AudioSegment.from_file(tts_path)
    softened = soften_voice(raw_tts)
    with open(alignment_json_path) as f:
        fragments = json.load(f)["fragments"]

    # detect TTS offset under start_chime
    tts_offset = detect_chime_tail(start_chime)
    tts_full = AudioSegment.silent(tts_offset) + softened
    tts_len = len(tts_full)

    # 5) Decide how long our final background needs to be:
    outro_len = len(end_chime)
    total_bg_len = len(intro_mix) + math.ceil(
        (tts_len - len(intro_mix)) / len(bg_loop)
    ) * len(bg_loop)
    total_bg_len = max(total_bg_len, tts_len + outro_len)

    # 6) Build that one full background track:
    reps = math.ceil((total_bg_len - len(intro_mix)) / len(bg_loop))
    looped_bg = build_seamless_loop(bg_loop, reps)
    full_bg = intro_mix + looped_bg[: (total_bg_len - len(intro_mix))]

    # 7) Build a curved fade manually
    tail = full_bg[-fade_ms:]
    n_frames = len(tail) // 100  # every 100ms
    curve = np.linspace(0, 1, n_frames) ** 2.5  # Quadratic/exponential fade (curvy)

    faded_tail = AudioSegment.silent(duration=0)
    for i in range(n_frames):
        start = i * 100
        end = min((i + 1) * 100, len(tail))
        slice_ = tail[start:end]
        gain = -curve[i] * 60  # fade from 0 dB to -60 dB
        faded_tail += slice_.apply_gain(gain)

    bg_faded = full_bg[:-fade_ms] + faded_tail

    # 8) Mix TTS and trigger chimes:
    base_mix = bg_faded.overlay(tts_full, position=0)
    for word, ms in extract_word_timings_from_fragments(
        fragments, offset_ms=tts_offset
    ):
        if word.lower().strip(".,!?") in TRIGGER_WORDS:
            base_mix = base_mix.overlay(
                normalize_volume(next_bar_chime(chosen["interchimes"]), -40.0),
                position=ms,
            )

    # 9) Overlay end chime _at_ the TTS end:
    final_chime = build_outro_segment(end_chime)
    base_mix = base_mix.overlay(final_chime, position=tts_len)

    # 10) Export
    out_path = os.path.join(OUTPUT_DIR, output_filename)
    base_mix.export(out_path, format="wav")

    return out_path
