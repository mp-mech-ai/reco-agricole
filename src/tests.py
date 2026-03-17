import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

VALID_DATA = {
    "rain (mm)": 534.0,
    "temp (C)": 14.74,
    "Year": 2013,
    "pesticides_tonnes": 45177.18,
    "Area": "Australia",
    "Days_to_Harvest": 104,
    "Irrigation_Used": True,
    "Fertilizer_Used": True,
    "Soil_Type": "Silt",
}

VALID_CROPS = {"Wheat", "Rice", "Maize"}

def make_mock_booster(return_value: float = 5000.0):
    booster = MagicMock()
    booster.predict.return_value = [return_value]
    return booster


@pytest.fixture()
def client():
    with patch("models_store.Models._load", return_value=make_mock_booster()):
        from api import app
        with TestClient(app) as c:
            yield c


# ---------------------------------------------------------------------------
# Root / health
# ---------------------------------------------------------------------------

def test_root(client):
    assert client.get("/").json() == {"message": "Hello World"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /predict – happy path
# ---------------------------------------------------------------------------

def test_predict_returns_yield(client):
    response = client.post("/predict", json={"crop": "Rice", "data": VALID_DATA})
    assert response.status_code == 200
    assert "yield" in response.json()
    assert isinstance(response.json()["yield"], float)


def test_predict_all_crops(client):
    for crop in ("Rice", "Wheat", "Maize"):
        response = client.post("/predict", json={"crop": crop, "data": VALID_DATA})
        assert response.status_code == 200, f"Failed for crop {crop}"
        assert "yield" in response.json()


# ---------------------------------------------------------------------------
# /predict – error cases
# ---------------------------------------------------------------------------

def test_predict_missing_crop_key(client):
    assert client.post("/predict", json={"data": VALID_DATA}).status_code == 422


def test_predict_missing_data_key(client):
    assert client.post("/predict", json={"crop": "Rice"}).status_code == 422


def test_predict_invalid_crop_name(client):
    response = client.post("/predict", json={"crop": "Tomato", "data": VALID_DATA})
    assert "error" in response.json()


def test_predict_bool_field_receives_float(client):
    bad = {**VALID_DATA, "Irrigation_Used": 12.0}
    assert "error" in client.post("/predict", json={"crop": "Rice", "data": bad}).json()


def test_predict_bool_field_receives_int(client):
    bad = {**VALID_DATA, "Fertilizer_Used": 1}
    assert "error" in client.post("/predict", json={"crop": "Rice", "data": bad}).json()


def test_predict_numeric_field_receives_string(client):
    bad = {**VALID_DATA, "rain (mm)": "heavy"}
    assert "error" in client.post("/predict", json={"crop": "Rice", "data": bad}).json()


def test_predict_year_receives_float(client):
    bad = {**VALID_DATA, "Year": 2013.5}
    assert "error" in client.post("/predict", json={"crop": "Rice", "data": bad}).json()


def test_predict_missing_field_in_data(client):
    bad = {k: v for k, v in VALID_DATA.items() if k != "Soil_Type"}
    assert "error" in client.post("/predict", json={"crop": "Rice", "data": bad}).json()


def test_predict_extra_field_in_data(client):
    bad = {**VALID_DATA, "unknown_field": 42}
    assert "error" in client.post("/predict", json={"crop": "Rice", "data": bad}).json()


# ---------------------------------------------------------------------------
# /recommend – happy path
# ---------------------------------------------------------------------------

def test_recommend_returns_item_and_yield(client):
    response = client.post("/recommend", json={"data": VALID_DATA})
    assert response.status_code == 200
    body = response.json()
    assert VALID_CROPS == set(body.keys())
    assert isinstance(body["Wheat"], float)


# ---------------------------------------------------------------------------
# /recommend – error cases
# ---------------------------------------------------------------------------

def test_recommend_missing_data_key(client):
    assert client.post("/recommend", json={}).status_code == 422


def test_recommend_bool_field_receives_float(client):
    bad = {**VALID_DATA, "Irrigation_Used": 0.0}
    assert "error" in client.post("/recommend", json={"data": bad}).json()


def test_recommend_missing_field(client):
    bad = {k: v for k, v in VALID_DATA.items() if k != "Area"}
    assert "error" in client.post("/recommend", json={"data": bad}).json()