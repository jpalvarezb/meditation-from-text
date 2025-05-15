import os
from app.logger import logger
from google.cloud import storage
from config.params import GCP_AUDIO_BUCKET, IS_PROD, AUDIO_ROOT

client = storage.Client()


def upload_to_gcs(
    local_path: str, bucket_name: str = GCP_AUDIO_BUCKET, dest_path: str = None
):
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")

    bucket = client.bucket(bucket_name)
    if dest_path:
        blob_path = dest_path
    else:
        if local_path.startswith(AUDIO_ROOT):
            # Preserve subfolder structure for project audio assets
            rel_path = os.path.relpath(local_path, AUDIO_ROOT)
            blob_path = rel_path.replace(os.sep, "/")
        else:
            # For files outside AUDIO_ROOT (e.g., /tmp), bucket folder = parent directory
            folder = os.path.basename(os.path.dirname(local_path))
            blob_path = f"{folder}/{os.path.basename(local_path)}"
    blob = bucket.blob(blob_path)

    blob.upload_from_filename(local_path)
    logger.info(f"Uploaded {local_path} to gs://{bucket_name}/{blob_path}")
    return f"gs://{bucket_name}/{blob_path}"


def fetch_from_gcs(gcs_path: str, local_path: str):
    if not gcs_path.startswith("gs://"):
        raise ValueError("GCS path must start with 'gs://'")

    parts = gcs_path.replace("gs://", "").split("/", 1)
    if len(parts) != 2:
        raise ValueError("Invalid GCS path format")

    bucket_name, blob_path = parts
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    blob.download_to_filename(local_path)
    logger.info(f"Downloaded {gcs_path} to {local_path}")


def resolve_asset(path: str) -> str:
    """
    Resolves a path to a local file.
    - If in dev mode, returns the original local path.
    - If in prod mode and the path starts with gs://, downloads it to /tmp and returns the local tmp path.
    """
    if not IS_PROD:
        return path

    if not path.startswith("gs://"):
        return path

    # Extract GCS bucket and blob path
    _, bucket_path = path.split("gs://", 1)
    bucket_name, *blob_parts = bucket_path.split("/")
    blob_path = "/".join(blob_parts)

    # Local destination
    tmp_path = os.path.join("/tmp", blob_path)
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)

    # Download from GCS
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    if not blob.exists():
        raise FileNotFoundError(f"GCS blob does not exist: {path}")

    blob.download_to_filename(tmp_path)
    logger.info(f"Downloaded {path} to {tmp_path}")
    return tmp_path
