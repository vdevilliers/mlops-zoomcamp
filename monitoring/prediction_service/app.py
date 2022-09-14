import mlflow
import os
import pickle
import requests
import pandas as pd

from mlflow.tracking import MlflowClient


from flask import Flask, request, jsonify
from pymongo import MongoClient


MONGODB_ADDRESS = os.getenv('MONGODB_ADRESS', "mongodb://127.0.0.1:27017")
EVIDENTLY_SERVICE_ADDRESS = os.getenv('EVIDENTLY_SERVICE', 'http://127.0.0.1:5000')

mongo_client = MongoClient(MONGODB_ADDRESS)
db = mongo_client.get_database("prediction_service")
collection = db.get_collection("data")

#fill in keys    
os.environ["AWS_ACCESS_KEY"] = ''
os.environ["AWS_SECRET_KEY"] = ''


TRACKING_SERVER_HOST = '' # fill in with the public DNS of the EC2 instance
mlflow.set_tracking_uri(f"http://{TRACKING_SERVER_HOST}:5000")
model = mlflow.statsmodels.load_model("models:/ARIMA/production")

app = Flask('percent increase')

                           
def save_to_db(record, prediction):
	rec = record.copy()
	rec['prediction'] = prediction
	collection.insert_one(rec)

def send_to_evidently_service(record, prediction):
	rec = record.copy()
	rec['prediction'] = prediction 
	requests.post(f'{EVIDENTLY_SERVICE_ADRESS}/iterate/historical', json=[rec])  

@app.route('/predict', methods=['POST'])
def predict_endpoint():
    record = request.get_json()
    val = record['nb_weeks']                    
    preds = model.forecast(val)
    prediction = list(preds)
    result = {'forecast': prediction}
    print(result)
    #save_to_db(record, result)
   #end_to_evidently_service(record, result)                                      
    return jsonify(result)

                      
                           

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=9696)
                           
