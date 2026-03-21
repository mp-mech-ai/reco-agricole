# Reco Agricole

Crop yield prediction and recommendation system. Given field conditions (region, soil type, rainfall, temperature, pesticides, etc.), the API predicts the expected yield for a specific crop or recommends the highest-yielding option across Maize, Rice, and Wheat.

You can view the dashboard at [https://agroreco.patarimi.duckdns.org/](https://agroreco.patarimi.duckdns.org/).

## Stack

| Layer | Technology |
|---|---|
| ML models | XGBoost (`.json` format) |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit + Plotly |
| Package manager | uv |
| Containerisation | Docker + Compose (local) |

## Project structure

```
.
├── src/
│   ├── models/             # Trained XGBoost model files
│   │   ├── maize_model.json
│   │   ├── rice_model.json
│   │   └── wheat_model.json
│   ├── models.py           # Model loading + validation + inference
│   ├── api.py              # FastAPI app
│   ├── webapp.py           # Streamlit dashboard
│   ├── tests.py            # pytest test suite
├── .streamlit/config.toml  # Streamlit config
├── notebooks/              # EDA, feature engineering, fine-tuning
├── data/
│   ├── raw/
│   └── processed/
├── Dockerfile.api
├── Dockerfile.webapp
├── docker-compose.yml
├── pyproject.toml
└── uv.lock
```

## Local development

**Requirements:** Python 3.12, [uv](https://docs.astral.sh/uv/)

```bash
# Install dependencies
uv sync

# Start the API
uv run fastapi run src/api.py

# In a second terminal, start the dashboard
uv run streamlit run src/webapp.py
```

The dashboard is available at `http://localhost:8501`. It expects the API at `http://localhost:8000` by default.

## Running tests

```bash
uv run pytest src/tests.py -v
```

## Local Docker

```bash
# Build and start both services
docker compose up -d --build

# View logs
docker compose logs -f api
docker compose logs -f webapp
```

| Service | URL |
|---|---|
| API | `http://localhost:8000` |
| API docs | `http://localhost:8000/docs` |
| Dashboard | `http://localhost:8501` |


## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Healthcheck |
| `POST` | `/predict` | Yield prediction for a specific crop |
| `POST` | `/recommend` | Best crop recommendation across all three |

**Predict payload example:**

```json
{
  "crop": "Rice",
  "data": {
    "rain (mm)": 534.0,
    "temp (C)": 14.74,
    "Year": 2013,
    "pesticides_tonnes": 45177.18,
    "Area": "Australia",
    "Days_to_Harvest": 104,
    "Irrigation_Used": true,
    "Fertilizer_Used": true,
    "Soil_Type": "Silt"
  }
}
```

**Recommend payload example:**
```json
{
  "data": {
    "rain (mm)": 534.0,
    "temp (C)": 14.74,
    "Year": 2013,
    "pesticides_tonnes": 45177.18,
    "Area": "Australia",
    "Days_to_Harvest": 104,
    "Irrigation_Used": true,
    "Fertilizer_Used": true,
    "Soil_Type": "Silt"
  }
}
```

## CI

GitHub Actions runs on every push and pull request to `main`:

1. **Test** — installs dependencies with `uv sync --frozen`, runs the full pytest suite
2. **Smoke test** — builds and starts the API via Docker Compose, waits for the healthcheck, then hits `/health` and `/predict` to verify the containerised build works end-to-end