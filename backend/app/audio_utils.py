import os
import random
import json
from pydub import AudioSegment
from app.cloud_utils import fetch_from_gcs
from pydub.effects import low_pass_filter, normalize
from config.params import CHIMES_DIR, AUDIO_ROOT, IS_PROD, GCP_AUDIO_BUCKET


def build_intro_layer(
    audio: AudioSegment, target_duration: int, fade_in_duration: int = 2000
) -> AudioSegment:
    """
    Loop and slice ambient/tone to ensure a full-duration intro layer,
    and apply a fade-in to the beginning.
    """
    if len(audio) < target_duration:
        repeats = (target_duration // len(audio)) + 1
        audio = audio * repeats
    intro = audio[:target_duration]
    return intro.fade_in(fade_in_duration)


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
    chime: AudioSegment, background: AudioSegment, start_ms: int
) -> AudioSegment:
    fade_out_duration = len(chime)

    # Slice background from start_ms to end of fade
    bg_tail = background[start_ms : start_ms + fade_out_duration]
    if len(bg_tail) < fade_out_duration:
        bg_tail += AudioSegment.silent(duration=fade_out_duration - len(bg_tail))

    bg_tail_faded = bg_tail.fade_out(fade_out_duration)
    return bg_tail_faded.overlay(chime)


def load_and_clean_audio_asset(rel_path: str, tmp_root: str = "/tmp") -> AudioSegment:
    """
    Loads an audio file from local or GCS, deletes the file and cleans up its empty parent dirs in prod.
    """
    full_path = os.path.normpath(os.path.join(AUDIO_ROOT, rel_path))
    rel_path = os.path.relpath(full_path, AUDIO_ROOT)

    if IS_PROD:
        bucket_subpath = rel_path.replace(os.sep, "/")
        gcs_path = f"gs://{GCP_AUDIO_BUCKET}/{bucket_subpath}"
        tmp_path = os.path.join(tmp_root, rel_path)
        os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
        fetch_from_gcs(gcs_path, tmp_path)
        audio = AudioSegment.from_file(tmp_path)
        try:
            os.remove(tmp_path)
            # Recursively remove empty parent dirs up to tmp_root
            dir_path = os.path.dirname(tmp_path)
            while dir_path != tmp_root:
                try:
                    os.rmdir(dir_path)
                    dir_path = os.path.dirname(dir_path)
                except OSError:
                    break
        except Exception:
            pass
        return audio

    local_path = os.path.join(AUDIO_ROOT, rel_path)
    return AudioSegment.from_file(local_path)


_chime_rotation = []
_last_interchime_folder = None


def next_bar_chime(
    chosen_interchime_folder: str, tmp_root: str = "/tmp"
) -> AudioSegment:
    global _chime_rotation, _last_interchime_folder

    if _last_interchime_folder != chosen_interchime_folder:
        _chime_rotation = []
        _last_interchime_folder = chosen_interchime_folder

    if not _chime_rotation:
        # Load manifest
        manifest_rel = f"chimes/{chosen_interchime_folder}/manifest.json"
        if IS_PROD:
            # Download manifest from GCS
            local_manifest = os.path.join(
                tmp_root, "chimes", chosen_interchime_folder, "manifest.json"
            )
            os.makedirs(os.path.dirname(local_manifest), exist_ok=True)
            fetch_from_gcs(f"gs://{GCP_AUDIO_BUCKET}/{manifest_rel}", local_manifest)
        else:
            # Read local manifest
            local_manifest = os.path.join(
                CHIMES_DIR, chosen_interchime_folder, "manifest.json"
            )

        with open(local_manifest, "r") as mf:
            files = json.load(mf)

        _chime_rotation = files.copy()
        random.shuffle(_chime_rotation)

    # Pop the next chime filename and load
    filename = _chime_rotation.pop(0)
    rel_audio = f"chimes/{chosen_interchime_folder}/{filename}"
    return load_and_clean_audio_asset(rel_audio, tmp_root=tmp_root)
