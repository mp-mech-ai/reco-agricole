import xgboost as xgb
import pandas as pd
from pathlib import Path
import shap 
import numpy as np

MODELS_DIR = Path(__file__).parent / "models"

VALID_CROPS = {"Wheat", "Rice", "Maize"}

COUNTRIES = [
    'Algeria', 'Angola', 'Argentina', 'Armenia', 'Australia', 'Austria', 'Azerbaijan',
    'Bahamas', 'Bangladesh', 'Belarus', 'Belgium', 'Botswana', 'Brazil', 'Bulgaria',
    'Burkina Faso', 'Burundi', 'Cameroon', 'Canada', 'Central African Republic', 'Chile',
    'Colombia', 'Croatia', 'Denmark', 'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador',
    'Eritrea', 'Estonia', 'Finland', 'France', 'Germany', 'Ghana', 'Greece', 'Guatemala',
    'Guinea', 'Guyana', 'Haiti', 'Honduras', 'Hungary', 'India', 'Indonesia', 'Iraq', 'Ireland',
    'Italy', 'Jamaica', 'Japan', 'Kazakhstan', 'Kenya', 'Latvia', 'Lebanon', 'Lesotho', 'Libya',
    'Lithuania', 'Madagascar', 'Malawi', 'Malaysia', 'Mali', 'Mauritania', 'Mauritius', 'Mexico',
    'Montenegro', 'Morocco', 'Mozambique', 'Namibia', 'Nepal', 'Netherlands', 'New Zealand',
    'Nicaragua', 'Niger', 'Norway', 'Pakistan', 'Papua New Guinea', 'Peru', 'Poland', 'Portugal',
    'Qatar', 'Romania', 'Rwanda', 'Saudi Arabia', 'Senegal', 'Slovenia', 'South Africa', 'Spain',
    'Sri Lanka', 'Sudan', 'Suriname', 'Sweden', 'Switzerland', 'Tajikistan', 'Thailand', 'Tunisia',
    'Turkey', 'Uganda', 'Ukraine', 'United Kingdom', 'Uruguay', 'Zambia', 'Zimbabwe',
]

SOIL_TYPES = ['Clay', 'Loam', 'Peaty', 'Sandy', 'Silt']

FIELD_TYPES: dict[str, type | tuple] = {
    "rain (mm)":         (int, float),
    "temp (C)":          (int, float),
    "Year":              int,
    "pesticides_tonnes": (int, float),
    "Area":              str,
    "Days_to_Harvest":   int,
    "Irrigation_Used":   bool,
    "Fertilizer_Used":   bool,
    "Soil_Type":         str,
}

FEATURE_GROUPS = {
    'rain (mm)':         ['rain (mm)'],
    'temp (C)':          ['temp (C)'],
    'Year':              ['Year'],
    'pesticides_tonnes': ['pesticides_tonnes'],
    'Days_to_Harvest':   ['Days_to_Harvest'],
    'Irrigation_Used':   ['Irrigation_Used'],
    'Fertilizer_Used':   ['Fertilizer_Used'],
    'Soil_Type':         [f'Soil_Type_{s}' for s in SOIL_TYPES],
    'Area':              [f'Area_{c}' for c in COUNTRIES],
}


class Models:
    def __init__(self, models_dir: Path = MODELS_DIR):
        self.Wheat = self._load(models_dir / "wheat_model.json")
        self.Rice  = self._load(models_dir / "rice_model.json")
        self.Maize = self._load(models_dir / "maize_model.json")

    @staticmethod
    def _load(path: Path) -> xgb.Booster:
        model = xgb.Booster()
        model.load_model(path)
        return model

    def _validate(self, raw_data: dict):
        expected = set(FIELD_TYPES.keys())
        received = set(raw_data.keys())

        missing = expected - received
        extra   = received - expected
        if missing or extra:
            raise ValueError(f"Invalid fields - missing: {missing}, unexpected: {extra}")

        for field, expected_type in FIELD_TYPES.items():
            value = raw_data[field]
            # bool is a subclass of int, so check bool fields strictly before numeric ones
            if expected_type is bool:
                if not isinstance(value, bool):
                    raise TypeError(
                        f"Field '{field}' must be bool, got {type(value).__name__}"
                    )
            elif not isinstance(value, expected_type):
                raise TypeError(
                    f"Field '{field}' must be {expected_type}, got {type(value).__name__}"
                )

    def _aggregate_shap(self, shap_array: np.ndarray, ohe_feature_names: list) -> dict:
        aggregated = {}
        for original_feat, ohe_cols in FEATURE_GROUPS.items():
            indices = [ohe_feature_names.index(c) for c in ohe_cols if c in ohe_feature_names]
            aggregated[original_feat] = float(np.sum(shap_array[indices]))
        return aggregated
    
    def predict(self, crop: str, raw_data: dict) -> dict:
        if crop not in VALID_CROPS:
            raise ValueError(f"Crop must be one of {VALID_CROPS}, got '{crop}'")
        self._validate(raw_data)
        data = self.transform_data(raw_data)
        model = getattr(self, crop)

        yield_predicted = float(model.predict(xgb.DMatrix(pd.DataFrame([data])))[0])
        return {"yield": yield_predicted}

    def predict_and_explain(self, crop: str, raw_data: dict) -> dict:
        if crop not in VALID_CROPS:
            raise ValueError(f"Crop must be one of {VALID_CROPS}, got '{crop}'")
        self._validate(raw_data)

        data_ohe = self.transform_data(raw_data)
        df_ohe   = pd.DataFrame([data_ohe])
        ohe_feature_names = list(data_ohe.keys())

        model = getattr(self, crop)
        yield_predicted = float(model.predict(xgb.DMatrix(df_ohe))[0])

        explainer  = shap.TreeExplainer(model=model)
        shap_array = explainer.shap_values(df_ohe)[0]  # shape (n_ohe_features,)

        shap_aggregated = self._aggregate_shap(shap_array, ohe_feature_names)

        return {
            "yield":       yield_predicted,
            "base_value":  float(explainer.expected_value),
            "shap_values": shap_aggregated,  # {"Area": 0.42, "Soil_Type": -0.18, ...}
            "raw_data":    raw_data,         # {"Area": "France", "Soil_Type": "Clay", ...}
        }

    def recommend(self, raw_data: dict) -> dict:
        self._validate(raw_data)
        data = self.transform_data(raw_data)

        yields = {
            crop: float(getattr(self, crop).predict(xgb.DMatrix(pd.DataFrame([data])))[0])
            for crop in VALID_CROPS
        }
        best = max(yields, key=yields.get)
        return {"item": best, "yield": yields[best]}

    def transform_data(self, input_dict: dict) -> dict:
        output_dict = {
            'rain (mm)':         input_dict['rain (mm)'],
            'temp (C)':          input_dict['temp (C)'],
            'Year':              input_dict['Year'],
            'pesticides_tonnes': input_dict['pesticides_tonnes'],
            'Days_to_Harvest':   input_dict['Days_to_Harvest'],
            'Irrigation_Used':   int(input_dict['Irrigation_Used']),
            'Fertilizer_Used':   int(input_dict['Fertilizer_Used']),
        }
        for country in COUNTRIES:
            output_dict[f'Area_{country}'] = 0
        for soil in SOIL_TYPES:
            output_dict[f'Soil_Type_{soil}'] = 0

        output_dict[f'Area_{input_dict["Area"]}']           = 1
        output_dict[f'Soil_Type_{input_dict["Soil_Type"]}'] = 1

        expected_order = [
            'rain (mm)', 'temp (C)', 'Year', 'pesticides_tonnes', 'Days_to_Harvest',
            'Irrigation_Used', 'Fertilizer_Used', 'Soil_Type_Clay', 'Soil_Type_Loam',
            'Soil_Type_Peaty', 'Soil_Type_Sandy', 'Soil_Type_Silt',
        ] + [f'Area_{c}' for c in COUNTRIES]

        return {key: output_dict[key] for key in expected_order}

if __name__ == "__main__":
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
    
    models = Models()

    print(models.predict_and_explain("Wheat", VALID_DATA))