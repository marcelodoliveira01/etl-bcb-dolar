import json
import os
import google.auth
from google.oauth2 import service_account
import pandas as pd
import pandas_gbq
import requests

# 1. Autenticação utilizando o Secret guardado no GitHub
gcp_credentials_json = os.environ.get("GCP_CREDENTIALS")

if gcp_credentials_json:
  info = json.loads(gcp_credentials_json)
  credentials = service_account.Credentials.from_service_account_info(info)
else:
  # Fallback caso rode localmente com credenciais padrão
  credentials, _ = google.auth.default()

# 2. Extração da API do Banco Central
url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.10813/dados?formato=json&dataInicial=01/01/2023"
response = requests.get(url)
response.raise_for_status()

data_json = response.json()
df_raw = pd.DataFrame(data_json)

# 3. Transformação com Pandas
df_transformed = df_raw.copy()
df_transformed.rename(
    columns={"data": "dt_cotacao", "valor": "vl_cotacao"}, inplace=True
)
df_transformed["dt_cotacao"] = pd.to_datetime(
    df_transformed["dt_cotacao"], format="%d/%m/%Y"
).dt.date
df_transformed["vl_cotacao"] = df_transformed["vl_cotacao"].astype(float)
df_transformed["dh_extracao"] = pd.Timestamp.now()

# 4. Carga no BigQuery
project_id = "meuprojeto-513012"
table_id = "dados_bcb.cotacao_dolar"

pandas_gbq.to_gbq(
    df_transformed,
    table_id,
    project_id=project_id,
    credentials=credentials,
    if_exists="replace",
)

print(
    f"ETL executado com sucesso! {len(df_transformed)} linhas enviadas para o"
    " BigQuery."
)
