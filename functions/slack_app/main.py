import datetime
import logging
import os

from flask import Request
from google.cloud import bigquery
from slack_bolt import App, Ack, Respond
from slack_bolt.adapter.google_cloud_functions import SlackRequestHandler
from slack_sdk.web import WebClient

logging.basicConfig(level=logging.ERROR)
app: App = App(process_before_response=True)
handler = SlackRequestHandler(app)


class Measurements:
    createdAt: datetime.datetime
    temperature: float
    humidity: float
    pressure: float
    gas_resistance: float

    def __init__(self, _created_at, _temperature, _humidity, _pressure, _gas_resistance):
        self.createdAt = _created_at
        self.temperature = _temperature
        self.humidity = _humidity
        self.pressure = _pressure
        self.gas_resistance = _gas_resistance


def make_slack_message(data: Measurements) -> str:
    if not data:
        return ""

    jst = datetime.timezone(datetime.timedelta(hours=9), "JST")

    now_hour = datetime.datetime.now(jst).hour
    if now_hour > 17:
        greet = "こんばんは :stars: "
    elif now_hour > 10:
        greet = "こんにちは :wave:"
    elif now_hour > 7:
        greet = ":sun_with_face: おはよう！"
    elif now_hour > 3:
        greet = ":sunrise: はやおきだね :sleepy:"
    else:
        greet = ":sleeping_accommodation: ねないの？ :melting_face:"

    float_format = "6.1f"
    measured_data = f"""
> *{data.createdAt.astimezone(jst).strftime("%Y/%m/%d %H:%M")}*
> 室温    {format(data.temperature, float_format)} ℃
> 湿度    {format(data.humidity, float_format)} %
> 気圧    {format(data.pressure, float_format)} hPa
> 気体抵抗 {format(data.gas_resistance, float_format)} KOhms
    """

    return f"{greet}\r{measured_data}"


def search_bq(table_id) -> Measurements | None:
    client = bigquery.Client()
    query = f"""
        SELECT createdAt, temperature, humidity, gas_resistance, pressure
        FROM `{table_id}` 
        WHERE createdAt > @searchDay
        ORDER BY createdAt DESC
        LIMIT 1
    """

    today_ts = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter(
            "searchDay", "TIMESTAMP", today_ts
        )]
    )
    query_job = client.query(query, job_config=job_config)

    for row in query_job:
        return Measurements(
            row.createdAt,
            row.temperature,
            row.humidity,
            row.pressure,
            row.gas_resistance
        )
    return


@app.command("/room-now")
def command_room_now(ack: Ack, respond: Respond):
    ack()

    table_id = os.environ.get('BIGQUERY_TABLE_ID', 'Specified environment variable is not set.')
    result = search_bq(table_id)
    message = make_slack_message(result)
    respond(message)


# Cloud Function
def entry_function(request: Request):
    request_json = request.get_json(silent=True)

    if request_json and 'channel' in request_json:
        channel = request_json['channel']
        table_id = os.environ.get('BIGQUERY_TABLE_ID', 'Specified environment variable is not set.')
        slack_api_token = os.environ.get('SLACK_BOT_TOKEN', 'Specified environment variable is not set.')

        result = search_bq(table_id)
        message = make_slack_message(result)

        client = WebClient(token=slack_api_token)
        response = client.chat_postMessage(text=message, channel=channel)
        print(response)
        return ""

    return handler.handle(request)
