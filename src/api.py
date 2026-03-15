from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from models import Models


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


@app.post("/predict")
async def predict(payload: PredictPayload):
    try:
        return app.state.models.predict(payload.crop, payload.data)
    except (TypeError, ValueError) as e:
        return JSONResponse(status_code=422, content={"error": str(e)})


@app.post("/recommend")
async def recommend(payload: RecommendPayload):
    try:
        return app.state.models.recommend(payload.data)
    except (TypeError, ValueError) as e:
        return JSONResponse(status_code=422, content={"error": str(e)})