import datetime
import logging
import os

from flask import Request
from google.cloud import firestore
from slack_bolt import App, Ack, Respond
from slack_bolt.adapter.google_cloud_functions import SlackRequestHandler
from slack_sdk.web import WebClient

logging.basicConfig(level=logging.ERROR)
app: App = App(process_before_response=True)


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
        return "no data"

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


def search_latest() -> Measurements:
    db = firestore.Client()
    latest_data = db.collection('room-monitor').document('latest').get()
    latest_dict = latest_data.to_dict()

    return Measurements(
        latest_dict['createdAt'],
        latest_dict['temperature'],
        latest_dict['humidity'],
        latest_dict['pressure'],
        latest_dict['gas_resistance']
    )


@app.command("/room-now")
def command_room_now(ack: Ack, respond: Respond):
    ack()

    result = search_latest()
    message = make_slack_message(result)
    respond(message)


# Cloud Function
def entry_function(request: Request):
    request_json = request.get_json(silent=True)

    if request_json and 'channel' in request_json:
        channel = request_json['channel']
        slack_api_token = os.environ.get('SLACK_BOT_TOKEN', 'Specified environment variable is not set.')

        result = search_latest()
        message = make_slack_message(result)

        client = WebClient(token=slack_api_token)
        response = client.chat_postMessage(text=message, channel=channel)
        print(response)
        return ""

    handler = SlackRequestHandler(app)
    return handler.handle(request)
