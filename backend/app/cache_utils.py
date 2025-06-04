import os
import json
import time
import hashlib
from typing import Any, Optional
from app.logger import logger
from app.cloud_utils import upload_to_gcs, fetch_from_gcs, generate_signed_url
from config.params import GCP_AUDIO_BUCKET, CACHE_DIR

# how long a cache entry stays fresh
CACHE_TTL_SECONDS = 24 * 3600


def _local_path(cache_key: str) -> str:
    return os.path.join(CACHE_DIR, f"{cache_key}.json")


def _remote_path(cache_key: str) -> str:
    return f"gs://{GCP_AUDIO_BUCKET}/cache/{cache_key}.json"


def generate_cache_key(journal_entry: str, duration: int, meditation_type: str) -> str:
    base = f"{journal_entry.strip()}::{duration}::{meditation_type}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def save_to_cache(cache_key: str, result: Any) -> None:
    """
    Wrap the result in a dict with created_at, write locally,
    upload to GCS under cache/, then delete the local copy.
    """
    payload = {
        "created_at": time.time(),
        "result": result,
    }
    local = _local_path(cache_key)
    # ensure parent dir exists
    os.makedirs(os.path.dirname(local), exist_ok=True)

    # write locally
    with open(local, "w") as f:
        json.dump(payload, f)

    # upload into gs://<bucket>/cache/<key>.json
    blob_path = f"cache/{cache_key}.json"
    try:
        upload_to_gcs(local, dest_path=blob_path)
    except Exception as e:
        logger.warning(f"Could not upload cache to GCS: {e}")

    # immediately delete local copy
    try:
        os.remove(local)
    except OSError:
        pass


def load_from_cache(cache_key: str) -> Optional[Any]:
    local = _local_path(cache_key)
    remote = _remote_path(cache_key)

    os.makedirs(os.path.dirname(local), exist_ok=True)

    if not os.path.exists(local):
        try:
            fetch_from_gcs(remote, local)
        except Exception:
            return None

    try:
        with open(local, "r") as f:
            payload = json.load(f)
    except Exception:
        try:
            os.remove(local)
        except OSError:
            pass
        return None

    try:
        os.remove(local)
    except OSError:
        pass

    created = payload.get("created_at", 0)
    if time.time() - created > CACHE_TTL_SECONDS:
        return None

    raw_result = payload.get("result")

    # If the result contains a GCS URI, regenerate the signed URL
    if isinstance(raw_result, str) and raw_result.startswith("gs://"):
        return generate_signed_url(raw_result)

    # Handle cases where result is a dict or list of URIs
    if isinstance(raw_result, dict):
        new_result = {}
        for k, v in raw_result.items():
            if k == "final_audio_path" and isinstance(v, str) and v.startswith("gs://"):
                new_result[k] = v
                new_result["final_signed_url"] = generate_signed_url(v)
            else:
                new_result[k] = v
        return new_result

    if isinstance(raw_result, list):
        return [
            generate_signed_url(v)
            if isinstance(v, str) and v.startswith("gs://")
            else v
            for v in raw_result
        ]

    return raw_result


def cache_exists(cache_key: str) -> bool:
    """
    True only if a *valid* cache entry is available (locally or on GCS).
    """
    return load_from_cache(cache_key) is not None
