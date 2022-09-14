from time import sleep
import pandas as pd
import requests



if __name__ == '__main__':
    time_horizons = [1,2,3,4,5,6,7,8,9,10,12,14,16,18,20,23,26,30]
  

    for horizon in time_horizons:
        previous_step = {'nb_weeks' :  int(horizon)}
        url = "http://127.0.0.1:9696/predict"
        response = requests.post(url, json=previous_step)
        print(response.json())
        sleep(5)