import mlflow
import os
from pydantic import BaseModel
import pandas as pd


mlflow.set_experiment("Reco Agricole")
mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI"))

class Models:
    def __init__(self, paths: dict):
        if not set(paths.keys()) == set(["Wheat", "Rice", "Maize"]):
            raise ValueError(
                "Model paths must be a dictionary with keys 'Wheat', 'Rice', and 'Maize'"
            )
        
        self.Wheat = mlflow.xgboost.load_model(paths["Wheat"])
        self.Rice = mlflow.xgboost.load_model(paths["Rice"])
        self.Maize = mlflow.xgboost.load_model(paths["Maize"])

    def predict(self, crop: str, raw_data: dict):
        if not set(raw_data.keys()) == set(["rain (mm)", "temp (C)", "Year", "pesticides_tonnes", "Area", "Days_to_Harvest", "Irrigation_Used", "Fertilizer_Used", "Soil_Type"]):
            raise ValueError(
                "Data must be a dictionary with keys 'rain (mm)', 'temp (C)', 'Year', 'pesticides_tonnes', 'Area', 'Days_to_Harvest', 'Irrigation_Used', 'Fertilizer_Used', 'Soil_Type'"
            )
        
        data = self.transform_data(raw_data)

        if crop == "Wheat":
            yield_pred = self.Wheat.predict(pd.DataFrame([data]))[0]
            return {"yield": float(yield_pred)}
        elif crop == "Rice":
            yield_pred = self.Rice.predict(pd.DataFrame([data]))[0]
            return {"yield": float(yield_pred)}
        elif crop == "Maize":
            yield_pred = self.Maize.predict(pd.DataFrame([data]))[0]
            return {"yield": float(yield_pred)}
        else:
            raise ValueError("Crop must be 'Wheat', 'Rice', or 'Maize'")
    
    def recommend(self, raw_data: dict):
        if not set(raw_data.keys()) == set(["rain (mm)", "temp (C)", "Year", "pesticides_tonnes", "Area", "Days_to_Harvest", "Irrigation_Used", "Fertilizer_Used", "Soil_Type"]):
            raise ValueError(
                "Data must be a dictionary with keys 'rain (mm)', 'temp (C)', 'Year', 'pesticides_tonnes', 'Area', 'Days_to_Harvest', 'Irrigation_Used', 'Fertilizer_Used', 'Soil_Type'"
            )
        
        data = self.transform_data(raw_data)
        
        wheat_yield = float(self.Wheat.predict(pd.DataFrame([data]))[0])
        rice_yield = float(self.Rice.predict(pd.DataFrame([data]))[0])
        maize_yield = float(self.Maize.predict(pd.DataFrame([data]))[0])


        # Returns the item that gives the highest yield
        if wheat_yield > rice_yield and wheat_yield > maize_yield:
            return {"item": "Wheat", "yield": wheat_yield}
        elif rice_yield > maize_yield:
            return {"item": "Rice", "yield": rice_yield}
        else:
            return {"item": "Maize", "yield": maize_yield}

    def transform_data(self, input_dict: dict):
        # Define all possible countries and soil types
        countries = [
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
            'Turkey', 'Uganda', 'Ukraine', 'United Kingdom', 'Uruguay', 'Zambia', 'Zimbabwe'
        ]

        soil_types = ['Clay', 'Loam', 'Peaty', 'Sandy', 'Silt']

        # Initialize the output dictionary with default values
        output_dict = {
            'rain (mm)': input_dict.get('rain (mm)'),
            'temp (C)': input_dict.get('temp (C)'),
            'Year': input_dict.get('Year'),
            'pesticides_tonnes': input_dict.get('pesticides_tonnes'),
            'Days_to_Harvest': input_dict.get('Days_to_Harvest'),
            'Irrigation_Used': int(input_dict.get('Irrigation_Used', 0)),
            'Fertilizer_Used': int(input_dict.get('Fertilizer_Used', 0)),
        }

        # Set all Area_Country fields to 0 by default
        for country in countries:
            output_dict[f'Area_{country}'] = 0

        # Set all Soil_Type fields to 0 by default
        for soil in soil_types:
            output_dict[f'Soil_Type_{soil}'] = 0

        # Set the correct Area_Country field to 1
        if 'Area' in input_dict:
            country = input_dict['Area']
            output_dict[f'Area_{country}'] = 1

        # Set the correct Soil_Type field to 1
        if 'Soil_Type' in input_dict:
            soil = input_dict['Soil_Type']
            output_dict[f'Soil_Type_{soil}'] = 1

        # Reorder the columns to match the model's expected order
        expected_order = [
            'rain (mm)', 'temp (C)', 'Year', 'pesticides_tonnes', 'Days_to_Harvest',
            'Irrigation_Used', 'Fertilizer_Used', 'Soil_Type_Clay', 'Soil_Type_Loam',
            'Soil_Type_Peaty', 'Soil_Type_Sandy', 'Soil_Type_Silt'
        ] + [f'Area_{country}' for country in countries]

        # Create a new dictionary with the correct order
        ordered_dict = {key: output_dict[key] for key in expected_order}

        return ordered_dict
