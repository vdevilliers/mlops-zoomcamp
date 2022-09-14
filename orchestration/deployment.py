import os
import mlflow
import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.ar_model import ar_select_order
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from hyperopt import STATUS_OK, Trials, fmin, hp, tpe
from hyperopt.pyll import scope
from prefect import flow, task
from prefect.deployments import Deployment
from prefect.orion.schemas.schedules import IntervalSchedule
from datetime import timedelta
import mlflow
from mlflow.tracking import MlflowClient
from mlflow.entities import ViewType



@task
def get_data(url, path_historical):
    
    def preprocess_df(df : pd.DataFrame, Date_column = 'Date') -> pd.DataFrame:     
        cols = list(df.iloc[2] + df.iloc[3])
        cols[2] = Date_column
        cols[0], cols[1] = 'todrop1', 'todrop2'
        df.columns = cols
        df = df.iloc[4:877]
        df = df[cols[2:]]
        df.columns 
        df.reset_index(inplace = True)
        df = df.drop('index', axis=1)
        df = df.sort_values(by='Date',ascending = True)
        df_ts = df.set_index('Date')
        return df_ts
      
    def ts_from_df(df : pd.DataFrame):
        ts = df.iloc[:,1].astype(float).pct_change()
        ts = 100 * ts.asfreq("7d").dropna()
        return ts

    os.system(os.path.join('wget '+url))
    xls = pd.ExcelFile(path_historical)
    df1 = pd.read_excel(xls, sheet_name = 'Prices wo taxes, EU')
    x1 = preprocess_df(df1)
    return ts_from_df(x1)

@task
def train_val_ts(data, SPLIT_SIZE = 18, N_PRED = 10):
    tscv = TimeSeriesSplit(SPLIT_SIZE, test_size = N_PRED)
    train = []
    test = []
    for train_index, test_index in tscv.split(data):
        train.append(np.array(data[0:train_index.max()]))
        test.append(np.array(data[train_index.max():test_index.max()+1]))
    return list(zip(train,test))


@task
def gen_best_model(samples):  
    def objective(params):
        with mlflow.start_run():
            p = params['p']
            d = params['d']
            q = params['q']
            best_mse = 100000
            steps_ahead = len(samples[0][1])
            for x,y in samples:
                arima_pdq = ARIMA(x, order=(p, d, q)).fit()
                forecast_ = arima_pdq.forecast(steps_ahead)
                current_mse = mean_squared_error(np.array(y[0:steps_ahead]), forecast_)
                if current_mse < best_mse :
                    best_model = arima_pdq
                    best_mse = current_mse

            mlflow.set_tag("model", "ARIMA")
            mlflow.log_params(params)
            #mlflow.log_metric('r2_score', best_r2)
            mlflow.log_metric('mse', best_mse)
            mlflow.statsmodels.log_model(best_model, 'model')

        return {'loss': best_mse, 'status': STATUS_OK}    

    search_space = {
            'p':  scope.int(hp.randint('p', 0,6)),
            'd' : scope.int(hp.randint('d', 0,2)),
            'q' : scope.int(hp.randint('q', 0,6))
                        }

    best_result = fmin(
            fn=objective,
            space=search_space,
            algo= tpe.suggest,
            max_evals=30,
            trials=Trials()       
            )
    
    
    runs = client.search_runs(
            experiment_ids="5",
            run_view_type=ViewType.ACTIVE_ONLY,
            max_results=5,
            order_by=["metrics.mse ASC"],
        )

    model_uri = f"runs:/{runs[0].info.run_id}/model"
    mlflow.register_model(
        model_uri=model_uri,
        name="ARIMA")

    new_stage = "Production"
    client.transition_model_version_stage(
    name="ARIMA", version=1, stage=new_stage, archive_existing_versions=True
    )
    
    return






@flow
def main(url = 'https://ec.europa.eu/energy/observatory/reports/Oil_Bulletin_Prices_History.xlsx',
             path_historical = './Oil_Bulletin_Prices_History.xlsx'):
    
    #fill in keys
    os.environ["AWS_ACCESS_KEY"] = ''
    os.environ["AWS_SECRET_KEY"] = ''
    TRACKING_SERVER_HOST = "" # fill in with the public DNS of the EC2 instance
    mlflow.set_tracking_uri(f"http://{TRACKING_SERVER_HOST}:5000")
    client = MlflowClient()
    data = get_data(url, path_historical)
    samples = train_val_ts(data)
    gen_best_model(samples)
    



deployment = Deployment.build_from_flow(
    flow=main,
    name="arima",
    schedule=IntervalSchedule(interval=timedelta(minutes=10080)),
    work_queue_name="ml",
)
   
    
deployment.apply()