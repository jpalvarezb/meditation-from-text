import os
import random
from pydub import AudioSegment
from config.params import CHIMES_DIR
from config.chime_variants import BAR_CHIME_VARIANTS
from pydub.effects import low_pass_filter, normalize


def build_intro_layer(audio: AudioSegment, target_duration: int) -> AudioSegment:
    """
    Loop and slice ambient/tone to ensure a full-duration intro layer.
    """
    if len(audio) < target_duration:
        repeats = (target_duration // len(audio)) + 1
        audio = audio * repeats
    return audio[:target_duration]


def normalize_volume(audio: AudioSegment, target_dBFS=-18.0) -> AudioSegment:
    change_in_dBFS = target_dBFS - audio.dBFS
    return audio.apply_gain(change_in_dBFS)


def choose_chime(filename: str, max_duration_ms: int = None) -> AudioSegment:
    path = os.path.join(CHIMES_DIR, filename)
    chime = AudioSegment.from_file(path)
    if max_duration_ms is not None:
        chime = chime[:max_duration_ms]
    return chime


def detect_chime_tail(
    chime_audio: AudioSegment, silence_threshold_dBFS=-40.0, min_tail_ms=2000
):
    chunk_size = 100  # ms
    last_loud_ms = min_tail_ms
    for i in range(min_tail_ms, len(chime_audio), chunk_size):
        chunk = chime_audio[i : i + chunk_size]
        if chunk.dBFS > silence_threshold_dBFS:
            last_loud_ms = i
    return last_loud_ms + 500


def soften_voice(voice_audio: AudioSegment) -> AudioSegment:
    voice = voice_audio - 2
    voice = low_pass_filter(voice, cutoff=4000)
    voice = normalize(voice)
    return voice


_chime_rotation = []


def next_bar_chime() -> AudioSegment:
    global _chime_rotation
    if not _chime_rotation:
        _chime_rotation = BAR_CHIME_VARIANTS[:]
        random.shuffle(_chime_rotation)
    filename = _chime_rotation.pop(0)
    path = os.path.join(CHIMES_DIR, filename)
    return AudioSegment.from_file(path)


def insert_pauses_simple(
    tts: AudioSegment,
    alignment: list,
    start_offset_ms=0,
    long_pause_after=(".",),
    short_pause_after=(",",),
    long_pause_ms=2000,
    short_pause_ms=700,
):
    output = tts
    inserts = []
    word_timings = []
    added_offset = 0

    for seg in alignment:
        word = seg.get("word", "").strip()
        end_ms = int(seg["end"] * 1000) + added_offset  # <-- Adjusted!
        word_timings.append((word, start_offset_ms + end_ms))

        if any(word.endswith(p) for p in long_pause_after):
            inserts.append((end_ms, long_pause_ms))
            added_offset += long_pause_ms
        elif any(word.endswith(p) for p in short_pause_after):
            inserts.append((end_ms, short_pause_ms))
            added_offset += short_pause_ms

    for insert_point, pause_ms in reversed(inserts):
        insert_point = min(insert_point, len(output))
        silence = AudioSegment.silent(duration=pause_ms)
        output = output[:insert_point] + silence + output[insert_point:]

    return output, word_timings


def extract_word_timings_from_fragments(fragments, offset_ms=0):
    """
    Converts Aeneas fragments into approximate word timings.
    Adds an optional start offset to each word.
    """
    word_timings = []

    for frag in fragments:
        text = " ".join(frag["lines"]).strip()
        if not text:
            continue

        start = float(frag["begin"]) * 1000 + offset_ms
        end = float(frag["end"]) * 1000 + offset_ms
        duration = end - start

        words = text.split()
        if not words:
            continue

        avg_word_duration = duration / len(words)

        for i, word in enumerate(words):
            word_end_time = start + (i + 1) * avg_word_duration
            word_timings.append((word, int(word_end_time)))

    return word_timings


def build_seamless_loop(
    base_loop: AudioSegment, repeats: int, crossfade_ms: int = 300
) -> AudioSegment:
    """
    Build a seamless ambient loop with tiny crossfade between repeats.
    """
    output = base_loop
    for _ in range(repeats - 1):
        output = output.append(base_loop, crossfade=crossfade_ms)
    return output


def build_outro_segment(
    end_chime: AudioSegment,
    background: AudioSegment,
    fade_out_duration: int = 8000,  # fade over 8 seconds
) -> AudioSegment:
    """
    Build the outro by fading out the tail of the actual background under the chime:
      1) Take the last `fade_out_duration` ms of `background`
      2) Fade that slice out
      3) Overlay it under the first `fade_out_duration` ms of the chime
      4) Append the rest of the chime so it rings alone
    """

    # 1) Ensure background is long enough
    if len(background) < fade_out_duration:
        repeats = (fade_out_duration // len(background)) + 1
        background = background * repeats

    # 2) Fade the last part of ambient
    ambient_tail = background[-fade_out_duration:].fade_out(fade_out_duration)

    # 3) Split chime into head (first fade_out_duration ms) and tail
    chime_head = end_chime[:fade_out_duration]
    chime_tail = end_chime[fade_out_duration:]

    # 4) Overlay ambient fade-out under chime head
    head_with_bg = chime_head.overlay(ambient_tail)

    # 5) Combine faded head + pure ringing tail
    return head_with_bg + chime_tail
