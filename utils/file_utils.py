"""
DeckClaude File Utilities

Provides: file type detection, safe filename generation, temp file management,
output directory creation, image downloading with retry, file size formatting.
"""

import hashlib
import logging
import mimetypes
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Optional, Union
import requests

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".json": "application/json",
    ".txt": "text/plain",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def detect_file_type(file_path: Union[str, Path]) -> str:
    """
    Detect file type from extension. Returns MIME type string.
    Falls back to 'application/octet-stream' for unknown types.
    """
    ext = Path(file_path).suffix.lower()
    return SUPPORTED_EXTENSIONS.get(ext, "application/octet-stream")


def is_supported_input(file_path: Union[str, Path]) -> bool:
    """Return True if file type is supported for processing."""
    ext = Path(file_path).suffix.lower()
    return ext in {".pdf", ".csv", ".xlsx", ".xls", ".json", ".txt"}


def safe_filename(text: str, max_length: int = 60, extension: str = "") -> str:
    """
    Convert arbitrary text to a filesystem-safe filename.
    Replaces special characters, collapses spaces, enforces length limit.

    Example:
        safe_filename("Q4 2024: Revenue & Growth Analysis!", ".pptx")
        → "Q4_2024_Revenue_Growth_Analysis.pptx"
    """
    # Remove characters that are unsafe in filenames
    cleaned = re.sub(r"[^\w\s\-]", "", text)
    # Collapse whitespace and replace with underscores
    cleaned = re.sub(r"\s+", "_", cleaned.strip())
    # Remove consecutive underscores
    cleaned = re.sub(r"_+", "_", cleaned)
    # Truncate
    cleaned = cleaned[:max_length].rstrip("_")
    if not cleaned:
        cleaned = "presentation"
    if extension and not extension.startswith("."):
        extension = "." + extension
    return cleaned + extension


def ensure_dir(path: Union[str, Path]) -> Path:
    """Create directory (and parents) if it doesn't exist. Returns the Path object."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_output_dir() -> Path:
    """Get the configured output directory, creating it if needed."""
    output_dir = Path(os.getenv("OUTPUT_DIR", "./output"))
    return ensure_dir(output_dir)


def get_assets_dir() -> Path:
    """Get the configured assets directory, creating it if needed."""
    assets_dir = Path(os.getenv("ASSETS_DIR", "./assets"))
    return ensure_dir(assets_dir)


def create_temp_file(suffix: str = ".tmp", prefix: str = "deckclaude_") -> str:
    """
    Create a temporary file and return its path.
    Caller is responsible for deletion.
    """
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
    os.close(fd)
    return path


def create_temp_dir(prefix: str = "deckclaude_") -> str:
    """Create a temporary directory and return its path."""
    return tempfile.mkdtemp(prefix=prefix)


def cleanup_temp_dir(path: Union[str, Path], ignore_errors: bool = True):
    """Remove a temporary directory and all its contents."""
    try:
        shutil.rmtree(str(path))
        logger.debug(f"Cleaned up temp dir: {path}")
    except Exception as e:
        if not ignore_errors:
            raise
        logger.debug(f"Could not clean up {path}: {e}")


def file_size_str(path: Union[str, Path]) -> str:
    """Return human-readable file size string: '1.4 MB', '340 KB', etc."""
    try:
        size = Path(path).stat().st_size
    except Exception:
        return "unknown size"

    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def content_hash(file_path: Union[str, Path]) -> str:
    """Compute MD5 hash of file contents for cache keying."""
    hasher = hashlib.md5()
    with open(str(file_path), "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_file_with_retry(
    url: str,
    dest_path: Union[str, Path],
    headers: Optional[dict] = None,
    max_retries: int = 3,
    timeout: int = 20,
    verify_ssl: bool = True,
) -> bool:
    """
    Download a file from URL to dest_path with exponential backoff retry.

    Args:
        url: Source URL
        dest_path: Local destination path
        headers: Optional HTTP headers (e.g., Authorization)
        max_retries: Number of retry attempts
        timeout: Request timeout in seconds
        verify_ssl: Whether to verify SSL certificates

    Returns:
        True on success, False on failure
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    last_error = None
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url,
                headers=headers or {},
                timeout=timeout,
                stream=True,
                verify=verify_ssl,
            )
            response.raise_for_status()

            with open(str(dest_path), "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.debug(f"Downloaded: {url} → {dest_path} ({file_size_str(dest_path)})")
            return True

        except requests.exceptions.HTTPError as e:
            # Don't retry on 4xx client errors
            if e.response and 400 <= e.response.status_code < 500:
                logger.warning(f"HTTP {e.response.status_code} for {url}: not retrying.")
                return False
            last_error = e

        except requests.exceptions.ConnectionError as e:
            last_error = e

        except requests.exceptions.Timeout as e:
            last_error = e
            logger.warning(f"Timeout on attempt {attempt + 1} for {url}")

        except Exception as e:
            last_error = e

        if attempt < max_retries - 1:
            wait = 2 ** attempt
            logger.warning(f"Download failed (attempt {attempt + 1}/{max_retries}), retrying in {wait}s: {last_error}")
            time.sleep(wait)

    logger.error(f"Download failed after {max_retries} attempts: {url} — {last_error}")
    # Clean up partial download
    if dest_path.exists():
        dest_path.unlink(missing_ok=True)
    return False


def find_files_by_extension(directory: Union[str, Path], extensions: set) -> list:
    """
    Recursively find all files with the given extensions in a directory.
    Returns sorted list of Path objects.
    """
    directory = Path(directory)
    found = []
    for ext in extensions:
        found.extend(directory.rglob(f"*{ext}"))
    return sorted(set(found))


def copy_file_to_output(src: Union[str, Path], dest_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Copy a file to the output directory (or specified dest_dir).
    Returns the destination path.
    """
    src = Path(src)
    if dest_dir is None:
        dest_dir = get_output_dir()
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(str(src), str(dest))
    return dest


def rotate_log_files(log_dir: Union[str, Path], max_files: int = 10, pattern: str = "*.log"):
    """Keep only the most recent N log files in a directory."""
    log_dir = Path(log_dir)
    if not log_dir.exists():
        return
    files = sorted(log_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    for old_file in files[max_files:]:
        try:
            old_file.unlink()
        except Exception:
            pass
