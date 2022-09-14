This is the final project for the [MLOps Zoomcamp](https://github.com/DataTalksClub/mlops-zoomcamp) course.
## Objective

We're trying to forecast future weekly oil prices using data from  https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en.
The base file is an xlxs that we preprocess to obtain a time series  (% increase or decrease) from 2005 to now (updated weekly).
We will use an **ARIMA(p,d,q)** (statsmodels package).
This project was entirely developped on the cloud (AWS EC2)

(make sure you fill in public dns & AWS keys in deployment.py and monitoring/prediction_service/app.py)
### Part 1-2-3
 Using **Mlflow**, we track performance with varying *p,d,q* before registering the best performing model.
 We can later access it using *mlflow.statsmodels.load_model()*.
 This is included into a fully deployed workflow using **Prefect**.
 #### setup :
##### For the mlflow part :
1.  have access to an S3 bucket
2.  give EC2 access to the ports used by prefect
3. start mlflow in a  separate terminal (orchestration folder)
 ##### For the Prefect part :
 Follow https://discourse.prefect.io/t/hosting-a-remote-orion-instance-on-a-cloud-vm/967
then : python deployment.py in a separate terminal (orchestration folder)

### Part 4-5 :
1. start mlflow in a separate terminal
2. open two separate terminals, go to the monitoring folder
3.  using conda activate _ per  https://www.youtube.com/watch?v=VkkpVXW53bo&list=PL3MmuxUbc_hIUISrluw_A7wDSmfOhErJK)
4. first terminal : docker-compose up --build  
5. second terminal :  python send_data.py in order to simulate traffic and generate forecasts

### Part 6+ :
todo
 