import os
import json
import shutil
import tempfile
from typing import Optional
from app.logger import logger
from urllib.parse import quote
from google.cloud import storage
from google.oauth2 import service_account
from config.params import (
    GCP_AUDIO_BUCKET,
    IS_PROD,
    IS_LOCAL_TEST,
    AUDIO_ROOT,
)

if IS_PROD and not IS_LOCAL_TEST:
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    )

    client = storage.Client(credentials=credentials)
elif IS_PROD and IS_LOCAL_TEST:
    credentials = service_account.Credentials.from_service_account_file(
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )

    client = storage.Client(credentials=credentials)
else:
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


def fetch_from_gcs(gcs_path: str, dest_path: Optional[str] = None) -> str:
    if not gcs_path.startswith("gs://"):
        raise ValueError("GCS path must start with 'gs://'")

    parts = gcs_path.replace("gs://", "").split("/", 1)
    if len(parts) != 2:
        raise ValueError("Invalid GCS path format")

    bucket_name, blob_path = parts
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    if dest_path is None:
        _, ext = os.path.splitext(blob_path)
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
        os.close(tmp_fd)
    else:
        tmp_path = dest_path

    blob.download_to_filename(tmp_path)
    logger.info(f"Downloaded {gcs_path} to temp file: {tmp_path}")
    return tmp_path


def resolve_asset(path: str, tmp_root: str = "/tmp") -> str:
    """
    Resolves a path to a local file.
    - In dev (IS_PROD=False), returns the original path.
    - In prod, if path starts with "gs://", downloads into tmp_root and returns that local path.
    """
    # If not in production or this isn't a GCS URI, just return as-is
    if not IS_PROD or not path.startswith("gs://"):
        return path

    # Split off "gs://bucket/..."
    _, bucket_path = path.split("gs://", 1)
    parts = bucket_path.split("/", 1)
    bucket_name = parts[0]
    blob_path = parts[1] if len(parts) == 2 else ""

    # Build a path under tmp_root that mirrors the blob's path
    local_dest = os.path.join(tmp_root, blob_path)
    os.makedirs(os.path.dirname(local_dest), exist_ok=True)

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    if not blob.exists():
        raise FileNotFoundError(f"GCS blob does not exist: {path}")

    blob.download_to_filename(local_dest)
    logger.info(f"Downloaded {path} to {local_dest}")
    return local_dest


def generate_signed_url(gcs_uri: str, expiration_minutes: int = 60) -> str:
    """
    Convert a gs://bucket/object URI into a signed HTTPS URL.
    Only used in production to allow public access to private GCS objects.
    """
    if not gcs_uri.startswith("gs://"):
        return gcs_uri

    from config.params import IS_PROD
    if not IS_PROD:
        return gcs_uri

    parts = gcs_uri[5:].split("/", 1)
    if len(parts) != 2:
        raise ValueError("Invalid GCS URI format")

    bucket_name, blob_name = parts
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=expiration_minutes * 60,
        method="GET",
        response_disposition=f'inline; filename="{quote(blob_name)}"',
    )
    return url


def clean_up_tmp_folder(tmp_root: str):
    """
    Completely delete the per‐request temp folder (tmp_root) and everything under it.
    """
    if not os.path.exists(tmp_root):
        logger.debug(f"No temp folder to clean up at {tmp_root}")
        return

    try:
        shutil.rmtree(tmp_root)
        logger.debug(f"Cleaned up temp folder {tmp_root}")
    except Exception as e:
        logger.warning(f"Failed to remove temp folder {tmp_root}: {e}")
