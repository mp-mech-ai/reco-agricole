from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from models_store import Models
from fastapi_limiter.depends import RateLimiter
from pyrate_limiter import Duration, Limiter, Rate

NUMBER_OF_REQUESTS = 10
NUMBER_OF_SECONDS = 30

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.models = Models()
    yield


app = FastAPI(lifespan=lifespan)


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


@app.post(
    "/predict",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(NUMBER_OF_REQUESTS, Duration.SECOND * NUMBER_OF_SECONDS))))]
    )
async def predict(payload: PredictPayload):
    try:
        return app.state.models.predict(payload.crop, payload.data)
    except (TypeError, ValueError) as e:
        return JSONResponse(status_code=422, content={"error": str(e)})

@app.post(
    "/predict_and_explain",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(NUMBER_OF_REQUESTS, Duration.SECOND * NUMBER_OF_SECONDS))))]
    )
async def predict_and_explain(payload: PredictPayload):
    try: 
        return app.state.models.predict_and_explain(payload.crop, payload.data)
    except (TypeError, ValueError) as e:
        return JSONResponse(status_code=422, content={"error": str(e)})

@app.post(
    "/recommend",
    dependencies=[Depends(RateLimiter(limiter=Limiter(Rate(NUMBER_OF_REQUESTS, Duration.SECOND * NUMBER_OF_SECONDS))))]
    )
async def recommend(payload: RecommendPayload):
    try:
        return app.state.models.recommend(payload.data)
    except (TypeError, ValueError) as e:
        return JSONResponse(status_code=422, content={"error": str(e)})