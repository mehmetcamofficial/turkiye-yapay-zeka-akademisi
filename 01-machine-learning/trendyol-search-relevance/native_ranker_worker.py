"""Fixed JSON-lines worker for experimental XGBoost ranker inference.

The worker intentionally owns the XGBoost/OpenMP runtime so the Streamlit
process can own PyTorch's separate OpenMP runtime without loading both.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np

REQUEST_VERSION = "1"
MAX_ROWS = 256
MAX_FEATURES = 128
ARTIFACTS = {
    "v2_ranker": Path(__file__).resolve().parent / "models/v2/search_ranker.pkl",
    "v21_ranker": Path(__file__).resolve().parent / "models/v2_1/v21_ranker_candidate.pkl",
}
_MODELS: dict[str, object] = {}


def _response(*, success: bool, results=None, latency=0.0, model_version="", artifact_version="", error_code=None, safe_error_message=""):
    return {
        "success": success,
        "results": results or [],
        "latency": round(float(latency), 6),
        "model_version": model_version,
        "artifact_version": artifact_version,
        "error_code": error_code,
        "safe_error_message": safe_error_message,
    }


def _model(name: str):
    if name not in ARTIFACTS:
        raise ValueError("unsupported_artifact")
    if name not in _MODELS:
        _MODELS[name] = joblib.load(ARTIFACTS[name])
    return _MODELS[name]


def handle(request: dict) -> dict:
    started = time.perf_counter()
    try:
        required = {"operation", "query", "top_k", "retrieval_method", "filters", "request_version"}
        if not isinstance(request, dict) or not required.issubset(request):
            raise ValueError("invalid_request")
        if request["request_version"] != REQUEST_VERSION or request["operation"] != "ranker_predict":
            raise ValueError("unsupported_request")
        if request["query"] not in ARTIFACTS or request["retrieval_method"] != "xgboost":
            raise ValueError("unsupported_request")
        values = np.asarray(request["filters"].get("features", []), dtype=np.float32)
        if values.ndim != 2 or not (1 <= values.shape[0] <= MAX_ROWS) or values.shape[1] > MAX_FEATURES:
            raise ValueError("payload_out_of_bounds")
        if not np.isfinite(values).all():
            raise ValueError("invalid_features")
        model = _model(request["query"])
        expected = int(model.get_booster().num_features())
        if values.shape[1] != expected:
            raise ValueError("feature_contract_mismatch")
        top_k = max(1, min(int(request["top_k"]), values.shape[0]))
        scores = np.asarray(model.predict(values), dtype=float)
        order = np.lexsort((np.arange(len(scores)), -scores))[:top_k]
        results = [{"row": int(i), "score": float(scores[i])} for i in order]
        return _response(success=True, results=results, latency=(time.perf_counter()-started)*1000,
                         model_version="XGBRanker", artifact_version=request["query"])
    except (ValueError, TypeError, KeyError):
        return _response(success=False, latency=(time.perf_counter()-started)*1000,
                         error_code="invalid_request", safe_error_message="Ranker request could not be validated.")
    except Exception:
        return _response(success=False, latency=(time.perf_counter()-started)*1000,
                         error_code="worker_inference_failed", safe_error_message="Experimental ranker is temporarily unavailable.")


def main() -> None:
    for line in sys.stdin:
        if len(line) > 512_000:
            result = _response(success=False, error_code="payload_too_large", safe_error_message="Ranker request is too large.")
        else:
            try:
                result = handle(json.loads(line))
            except json.JSONDecodeError:
                result = _response(success=False, error_code="invalid_json", safe_error_message="Ranker request could not be decoded.")
        sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
