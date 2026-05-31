# -*- coding: utf-8 -*-
import os
import base64
import hashlib
import pathlib


CHUNK_SIZE = 256 * 1024  # 256 КБ


class FileReceiver:
    """Принимает файл по частям от контроллера."""

    def __init__(self):
        self._transfers: dict[str, dict] = {}

    def begin(self, transfer_id: str, dest_path: str, total_size: int, chunks: int):
        self._transfers[transfer_id] = {
            "path": pathlib.Path(dest_path),
            "total": total_size,
            "chunks": chunks,
            "received": 0,
            "handle": None,
        }
        t = self._transfers[transfer_id]
        t["path"].parent.mkdir(parents=True, exist_ok=True)
        t["handle"] = open(t["path"], "wb")
        return {"type": "file_begin_ack", "id": transfer_id}

    def chunk(self, transfer_id: str, index: int, data_b64: str) -> dict:
        t = self._transfers.get(transfer_id)
        if not t:
            return {"type": "file_error", "id": transfer_id, "reason": "unknown_id"}
        chunk_bytes = base64.b64decode(data_b64)
        t["handle"].write(chunk_bytes)
        t["received"] += len(chunk_bytes)
        progress = int(t["received"] / t["total"] * 100)
        return {"type": "file_progress", "id": transfer_id, "progress": progress}

    def finish(self, transfer_id: str, md5: str) -> dict:
        t = self._transfers.pop(transfer_id, None)
        if not t:
            return {"type": "file_error", "id": transfer_id, "reason": "unknown_id"}
        t["handle"].close()

        actual_md5 = hashlib.md5(t["path"].read_bytes()).hexdigest()
        if actual_md5 != md5:
            t["path"].unlink(missing_ok=True)
            return {"type": "file_error", "id": transfer_id, "reason": "checksum_mismatch"}

        return {"type": "file_done", "id": transfer_id, "path": str(t["path"])}


class FileSender:
    """Читает файл и отдаёт его по частям контроллеру."""

    @staticmethod
    def prepare(src_path: str) -> dict:
        p = pathlib.Path(src_path)
        if not p.exists():
            return {"type": "file_error", "reason": "not_found", "path": src_path}
        size = p.stat().st_size
        chunks = (size + CHUNK_SIZE - 1) // CHUNK_SIZE
        md5 = hashlib.md5(p.read_bytes()).hexdigest()
        return {
            "type": "file_send_begin",
            "path": src_path,
            "name": p.name,
            "size": size,
            "chunks": chunks,
            "md5": md5,
        }

    @staticmethod
    def read_chunks(src_path: str):
        with open(src_path, "rb") as f:
            index = 0
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield index, base64.b64encode(chunk).decode()
                index += 1
