"""Persistent, bounded client for the isolated experimental ranker worker."""
from __future__ import annotations

import json
import logging
import select
import subprocess
import sys
import threading
import atexit
from dataclasses import dataclass

import numpy as np
import streamlit as st

from portfolio.config import TRENDYOL_RELEVANCE_DIR

LOGGER = logging.getLogger(__name__)
TIMEOUT_SECONDS = 12.0


@dataclass
class RankerWorker:
    process: subprocess.Popen
    lock: threading.Lock

    def request(self, payload: dict) -> dict:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > 512_000:
            raise RuntimeError("Ranker request is too large.")
        with self.lock:
            if self.process.poll() is not None:
                raise RuntimeError("Experimental ranker worker is unavailable.")
            assert self.process.stdin is not None and self.process.stdout is not None
            self.process.stdin.write(encoded + "\n")
            self.process.stdin.flush()
            ready, _, _ = select.select([self.process.stdout], [], [], TIMEOUT_SECONDS)
            if not ready:
                self.process.kill()
                raise RuntimeError("Experimental ranker request timed out.")
            response = json.loads(self.process.stdout.readline())
        if not response.get("success"):
            LOGGER.warning("Ranker worker error code: %s", response.get("error_code"))
            raise RuntimeError(response.get("safe_error_message") or "Experimental ranker is unavailable.")
        return response

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()


@st.cache_resource(show_spinner=False)
def ranker_worker() -> RankerWorker:
    entry = TRENDYOL_RELEVANCE_DIR / "native_ranker_worker.py"
    process = subprocess.Popen(
        [sys.executable, str(entry)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, bufsize=1, close_fds=True,
    )
    worker=RankerWorker(process, threading.Lock())
    atexit.register(worker.close)
    return worker


def ranker_predict(features, artifact: str = "v21_ranker", top_k: int = 10) -> dict:
    values = np.asarray(features, dtype=np.float32)
    payload = {
        "operation": "ranker_predict", "query": artifact, "top_k": int(top_k),
        "retrieval_method": "xgboost", "filters": {"features": values.tolist()},
        "request_version": "1",
    }
    return ranker_worker().request(payload)
