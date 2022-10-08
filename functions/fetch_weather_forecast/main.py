import json
import os
import urllib.request

import functions_framework
from google.cloud import bigquery


def load_bq(json_data, table_id: str):
    # BigQueryにロード
    client = bigquery.Client()
    job_config = bigquery.LoadJobConfig(
        autodetect=True,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    )
    load_job = client.load_table_from_json(
        [json_data], table_id, job_config=job_config
    )
    load_job.result()  # Waits for the job to complete.
    destination_table = client.get_table(table_id)
    print("Loaded {} rows to {}.".format(destination_table.num_rows, table_id))


def fetch_average_data(json_data):
    average_data: dict = {}
    for row in json_data:
        average_data['reportDatetime'] = row['reportDatetime']

        if 'tempAverage' in row:
            average_data['tempAverage'] = row['tempAverage']

        if 'precipAverage' in row:
            average_data['precipAverage'] = row['precipAverage']

    return average_data


def fetch_temps_data(json_data):
    temps_data: dict = {}
    for row in json_data:
        temps_data['reportDatetime'] = row['reportDatetime']

        timeSeries = row['timeSeries']
        for item in timeSeries:
            areas = item['areas']
            for area in areas:
                if 'tempsMin' in area:
                    temps_data['temps'] = item
                    break

    return temps_data


def load_overview(fetch_url: str, table_id: str) -> None:
    request = urllib.request.Request(fetch_url)
    with urllib.request.urlopen(request) as response:
        json_data = json.loads(response.read().decode("utf-8"))
        load_bq(json_data, table_id)


def load_weather(fetch_url: str, forecast_average_table_id: str, forecast_temps_table_id: str) -> None:
    request = urllib.request.Request(fetch_url)
    with urllib.request.urlopen(request) as response:
        json_data = json.loads(response.read().decode("utf-8"))
        average_data: dict = fetch_average_data(json_data)
        temps_data: dict = fetch_temps_data(json_data)

        load_bq(average_data, forecast_average_table_id)
        load_bq(temps_data, forecast_temps_table_id)


@functions_framework.cloud_event
def fetch_weather_forecast(cloud_event):
    NOT_DEFINED_VAR = 'Specified environment variable is not set.'

    overview_url = os.environ.get('OVERVIEW_FORECAST_URL', NOT_DEFINED_VAR)
    overview_table_id = os.environ.get('OVERVIEW_TABLE_ID', NOT_DEFINED_VAR)
    load_overview(overview_url, overview_table_id)

    forecast_url = os.environ.get('FORECAST_URL', NOT_DEFINED_VAR)
    forecast_average_table_id = os.environ.get('FORECAST_AVERAGE_TABLE_ID', NOT_DEFINED_VAR)
    forecast_temps_table_id = os.environ.get('FORECAST_TEMPS_TABLE_ID', NOT_DEFINED_VAR)
    load_weather(forecast_url, forecast_average_table_id, forecast_temps_table_id)
