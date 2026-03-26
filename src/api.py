import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from models_store import Models
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

NUMBER_OF_REQUESTS = 10
NUMBER_OF_SECONDS = 30
MAX_LOG_ENTRIES = 200  # cap so memory doesn't grow unbounded during a demo session

# Set DISABLE_RATE_LIMIT=true to bypass rate limiting (e.g. during tests).
_RATE_LIMIT_ENABLED = os.getenv("DISABLE_RATE_LIMIT", "false").lower() != "true"
_RATE_LIMIT_STRING = f"{NUMBER_OF_REQUESTS}/{NUMBER_OF_SECONDS} seconds"

limiter = Limiter(key_func=get_remote_address)


def rate_limit(func):
    """Decorator that applies the shared rate limit unless DISABLE_RATE_LIMIT=true."""
    if not _RATE_LIMIT_ENABLED:
        return func
    return limiter.limit(_RATE_LIMIT_STRING)(func)


# ── In-memory store ────────────────────────────────────────────────────────────


@dataclass
class UsageMetrics:
    total_calls: int = 0
    calls_by_endpoint: dict = field(default_factory=lambda: defaultdict(int))
    calls_by_crop: dict = field(default_factory=lambda: defaultdict(int))
    errors: int = 0
    logs: list = field(default_factory=list)

    def record(
        self,
        endpoint: str,
        input_obj=None,
        output_obj=None,
        crop: str | None = None,
        error: bool = False,
    ):
        self.total_calls += 1
        self.calls_by_endpoint[endpoint] += 1
        if crop:
            self.calls_by_crop[crop] += 1
        if error:
            self.errors += 1

        output_text = str(output_obj) if output_obj is not None else "—"
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "endpoint": endpoint,
            "crop": crop or "—",
            "input": str(input_obj) if input_obj is not None else "—",
            "output": output_text if error else output_text,
        }
        self.logs.insert(0, entry)  # newest first
        if len(self.logs) > MAX_LOG_ENTRIES:
            self.logs.pop()


# ── App ────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.models = Models()
    app.state.metrics = UsageMetrics()
    yield


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter


# Record 429s in metrics before returning the standard rate-limit response.
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    endpoint = request.url.path.lstrip("/")
    request.app.state.metrics.record(
        endpoint, error=True, output_obj="Rate limit exceeded"
    )
    return JSONResponse(
        status_code=429,
        content={"error": "Rate limit reached - please wait a moment before retrying."},
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)


class PredictPayload(BaseModel):
    crop: str
    data: dict


class RecommendPayload(BaseModel):
    data: dict


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    m = app.state.metrics
    return {
        "total_calls": m.total_calls,
        "calls_by_endpoint": dict(m.calls_by_endpoint),
        "calls_by_crop": dict(m.calls_by_crop),
        "errors": m.errors,
        "error_rate": round(m.errors / m.total_calls, 2) if m.total_calls else 0,
        "logs": m.logs,
    }


@app.post("/predict")
@rate_limit
async def predict(request: Request, payload: PredictPayload):
    try:
        result = app.state.models.predict(payload.crop, payload.data)
        app.state.metrics.record("predict", payload.data, result, crop=payload.crop)
        return result
    except (TypeError, ValueError) as e:
        app.state.metrics.record(
            "predict", payload.data, str(e), crop=payload.crop, error=True
        )
        return JSONResponse(status_code=422, content={"error": str(e)})


@app.post("/predict_and_explain")
@rate_limit
async def predict_and_explain(request: Request, payload: PredictPayload):
    try:
        result = app.state.models.predict_and_explain(payload.crop, payload.data)
        app.state.metrics.record(
            "predict_and_explain", payload.data, result, crop=payload.crop
        )
        return result
    except (TypeError, ValueError) as e:
        app.state.metrics.record(
            "predict_and_explain", payload.data, str(e), crop=payload.crop, error=True
        )
        return JSONResponse(status_code=422, content={"error": str(e)})


@app.post("/recommend")
@rate_limit
async def recommend(request: Request, payload: RecommendPayload):
    try:
        result = app.state.models.recommend(payload.data)
        app.state.metrics.record("recommend", payload.data, result)
        return result
    except (TypeError, ValueError) as e:
        app.state.metrics.record("recommend", payload.data, str(e), error=True)
        return JSONResponse(status_code=422, content={"error": str(e)})
