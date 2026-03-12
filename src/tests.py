from fastapi.testclient import TestClient
from api import app
from models import Models

def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.json() == {"message": "Hello World"}

def test_predict_good_format():
    payload = {
        "crop": "Rice",
        "data": {
            "rain (mm)": 534.0,
            "temp (C)": 14.74,
            "Year": 2013,
            "pesticides_tonnes": 45177.18,
            "Area": "Australia",
            "Days_to_Harvest": 104,
            "Irrigation_Used": True,
            "Fertilizer_Used": True,
            "Soil_Type": "Silt"
        }
    }

    client = TestClient(app)
    response = client.post("/predict", json=payload)
    print(response.json())
    assert "yield" in response.json()

if __name__ == "__main__":
    models = Models({
        "Maize": "models:/model-Maize/None",
        "Rice": "models:/model-Rice/None",
        "Wheat": "models:/model-Wheat/None"
    })

    result = models.predict("Rice", {
            "rain (mm)": 534.0,
            "temp (C)": 14.74,
            "Year": 2013,
            "pesticides_tonnes": 45177.18,
            "Area": "Australia",
            "Days_to_Harvest": 104,
            "Irrigation_Used": True,
            "Fertilizer_Used": True,
            "Soil_Type": "Silt"
        }
    )

    print(result)
