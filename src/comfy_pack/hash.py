import os
import json
import hashlib
import asyncio
from typing import Dict, List
from datetime import datetime
import fcntl
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import multiprocessing
from .const import SHA_CACHE_FILE


def calculate_sha256_worker(filepath: str, chunk_size: int = 4 * 1024 * 1024) -> str:
    """Calculate SHA-256 in a separate process"""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_sha256(filepath: str) -> str:
    """
    Synchronously calculate SHA-256 for a file with automatic caching

    Args:
        filepath: File path to calculate SHA-256 for

    Returns:
        SHA-256 hash of the file (None for nonexistent files)
    """
    return batch_get_sha256([filepath])[filepath]


def async_get_sha256(filepath: str) -> str:
    """
    Asynchronously calculate SHA-256 for a file with automatic caching

    Args:
        filepath: File path to calculate SHA-256 for

    Returns:
        SHA-256 hash of the file (None for nonexistent files)
    """
    return asyncio.run(async_batch_get_sha256([filepath]))[filepath]


def batch_get_sha256(filepaths: List[str]) -> Dict[str, str]:
    """
    Synchronously calculate SHA-256 for multiple files with automatic caching

    Args:
        filepaths: List of file paths to calculate SHA-256 for

    Returns:
        Dictionary mapping filepath to SHA-256 hash (None for nonexistent files)
    """
    return asyncio.run(async_batch_get_sha256(filepaths))


async def async_batch_get_sha256(filepaths: List[str]) -> Dict[str, str]:
    """
    Asynchronously calculate SHA-256 for multiple files with automatic caching

    Args:
        filepaths: List of file paths to calculate SHA-256 for

    Returns:
        Dictionary mapping filepath to SHA-256 hash (None for nonexistent files)
    """
    # Load cache
    cache = {}
    if SHA_CACHE_FILE.exists():
        try:
            with SHA_CACHE_FILE.open("r") as f:
                cache = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    # Initialize process pool
    max_workers = max(1, multiprocessing.cpu_count() - 1)

    # Process files
    results = {}
    async with asyncio.Lock():
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            loop = asyncio.get_event_loop()

            for filepath in filepaths:
                if not os.path.exists(filepath):
                    results[filepath] = None
                    continue

                # Get file info
                stat = os.stat(filepath)
                current_size = stat.st_size
                current_time = stat.st_birthtime

                # Check cache
                cache_entry = cache.get(filepath)
                if cache_entry:
                    if (
                        cache_entry["size"] == current_size
                        and cache_entry["birthtime"] == current_time
                    ):
                        results[filepath] = cache_entry["sha256"]
                        continue

                # Calculate new SHA
                calc_func = partial(calculate_sha256_worker, filepath)
                sha256 = await loop.run_in_executor(pool, calc_func)

                # Update cache and results
                cache[filepath] = {
                    "sha256": sha256,
                    "size": current_size,
                    "birthtime": current_time,
                    "last_verified": datetime.now().isoformat(),
                }
                results[filepath] = sha256

    # Save cache
    try:
        with SHA_CACHE_FILE.open("w") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(cache, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (IOError, OSError):
        pass

    return results
