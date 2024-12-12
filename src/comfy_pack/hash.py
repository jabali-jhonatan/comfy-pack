from __future__ import annotations

import contextlib
import hashlib
import json
from datetime import datetime
from typing import TypedDict

import anyio

from .const import SHA_CACHE_FILE


class ModelCache(TypedDict):
    sha256: str
    size: int
    birthtime: float
    last_verified: str


class ModelHashes:
    def __init__(self) -> None:
        self._data: dict[str, ModelCache] = {}

    async def load(self) -> None:
        path = anyio.Path(SHA_CACHE_FILE)
        if not await path.exists():
            return
        async with await path.open("r") as f:
            self._data = json.loads(await f.read())

    async def save(self) -> None:
        with contextlib.suppress(OSError):
            async with await anyio.open_file(SHA_CACHE_FILE, "w") as f:
                await f.write(json.dumps(self._data, indent=2))

    async def get(self, filepath: str, cache_only: bool = False) -> str:
        afile = anyio.Path(filepath)
        stat = await afile.stat()
        entry = self._data.get(filepath)
        if (
            entry is not None
            and entry["size"] == stat.st_size
            and entry["birthtime"] == stat.st_ctime
        ):
            return entry["sha256"]
        if cache_only:
            return ""
        sha256 = await self.calculate_sha256(filepath)
        self._data[filepath] = {
            "sha256": sha256,
            "size": stat.st_size,
            "birthtime": stat.st_ctime,
            "last_verified": datetime.now().isoformat(),
        }
        return sha256

    async def calculate_sha256(self, filepath: str, chunk_size: int = 8192) -> str:
        async with await anyio.open_file(filepath, "rb") as f:
            sha256 = hashlib.sha256()
            while chunk := await f.read(chunk_size):
                sha256.update(chunk)
            return sha256.hexdigest()
