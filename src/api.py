from fastapi import FastAPI
from models import Models

app = FastAPI()

models = Models({
    "Maize": "models:/model-Maize/None",
    "Rice": "models:/model-Rice/None",
    "Wheat": "models:/model-Wheat/None"
})

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/predict", response_model=dict)
async def predict(payload: dict):
    if "crop" in payload and "data" in payload:
        output = models.predict(payload["crop"], payload["data"])
        return output
    else:
        return {"error": "Missing crop or data"}

@app.post("/recommend", response_model=dict)
async def recommend(payload: dict):
    if "data" in payload:
        return models.recommend(payload["data"])
