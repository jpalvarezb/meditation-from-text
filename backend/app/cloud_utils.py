import os
from app.logger import logger
from google.cloud import storage
from config.params import AUDIO_BUCKET

client = storage.Client()


def upload_to_gcs(
    local_path: str, bucket_name: str = AUDIO_BUCKET, dest_path: str = None
):
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"Local file not found: {local_path}")

    bucket = client.bucket(bucket_name)
    blob_path = dest_path or os.path.basename(local_path)
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
