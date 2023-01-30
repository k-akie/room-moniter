import datetime
import os

import functions_framework
from google.cloud import bigquery
from google.cloud import firestore
from slack_sdk.web import WebClient


def send_slack(message: str):
    slack_channel = os.environ.get('SLACK_CHANNEL', 'Specified environment variable is not set.')
    slack_api_token = os.environ.get('SLACK_BOT_TOKEN', 'Specified environment variable is not set.')
    client = WebClient(token=slack_api_token)
    response = client.chat_postMessage(text=message, channel=slack_channel)
    print(response)


def warning_cold(temperature: float):
    too_cold_temperature = 20

    db = firestore.Client()
    latest_ref = db.collection('room-monitor').document('warning')
    latest_dic = latest_ref.get().to_dict()

    # 寒すぎリセット
    if temperature > too_cold_temperature + 3:
        latest_ref.update(
            {
                'updated': firestore.SERVER_TIMESTAMP,
                'temperature': temperature,
                'too_cold': False,
            }
        )
        return

    # 寒すぎない
    if temperature > too_cold_temperature:
        return

    # ずっと寒すぎ
    if latest_dic['too_cold']:
        return

    # 寒すぎ
    latest_ref.update(
        {
            'updated': firestore.SERVER_TIMESTAMP,
            'temperature': temperature,
            'too_cold': True,
            'too_hot': False,
        }
    )
    send_slack(f"{too_cold_temperature}度を下回りました :cold_face:")


def warning_hot(temperature: float):
    too_hot_temperature = 30

    db = firestore.Client()
    latest_ref = db.collection('room-monitor').document('warning')
    latest_dic = latest_ref.get().to_dict()

    # 暑すぎリセット
    if temperature < too_hot_temperature - 3:
        latest_ref.update(
            {
                'updated': firestore.SERVER_TIMESTAMP,
                'temperature': temperature,
                'too_hot': False,
            }
        )
        return

    # 暑すぎない
    if temperature < too_hot_temperature:
        return

    # ずっと暑すぎ
    if latest_dic['too_hot']:
        return

    # 暑すぎ
    latest_ref.update(
        {
            'updated': firestore.SERVER_TIMESTAMP,
            'temperature': temperature,
            'too_cold': False,
            'too_hot': True,
        }
    )
    send_slack(f"{too_hot_temperature}度を上回りました :hot_face:")


def insert_bq(dt_now_iso, request_json) -> bool:
    rows_to_insert = [{
        'createdAt': dt_now_iso,
        'temperature': request_json['temperature'],  # 温度(℃)
        'pressure': request_json['pressure'],  # 気圧(hPa)
        'humidity': request_json['humidity'],  # 湿度(%)
        'gas_resistance': request_json['gas_resistance'],  # 気体抵抗(KOhms)
        'elevation': request_json['elevation']  # 標高(m)
    }]

    table_id = os.environ.get('BIGQUERY_TABLE_ID', 'Specified environment variable is not set.')

    client = bigquery.Client()
    table = client.get_table(table_id)
    errors = client.insert_rows(table, rows_to_insert)
    if errors:
        print("Encountered errors while inserting rows: {}".format(errors))
        return False
    return True


def update_latest_fs(dt_now_iso, request_json):
    db = firestore.Client()
    latest_data = db.collection('room-monitor').document('latest')
    latest_data.update(
        {
            'createdAt': dt_now_iso,
            'temperature': request_json['temperature'],  # 温度(*C)
            'pressure': request_json['pressure'],  # 気圧(hPa)
            'humidity': request_json['humidity'],  # 湿度(%)
            'gas_resistance': request_json['gas_resistance'],  # (KOhms)
            'elevation': request_json['elevation']  # 標高(m)
        }
    )


@functions_framework.http
def register_monitoring_data(request):
    request_json = request.get_json(silent=True)
    dt_now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    dt_now_iso = dt_now.isoformat()
    print(request_json, dt_now_iso)

    if insert_bq(dt_now_iso, request_json):
        update_latest_fs(dt_now, request_json)

        # 10～21時代だけ暑すぎ・寒すぎ警告する
        jst = datetime.timezone(datetime.timedelta(hours=9), "JST")
        now_hour = datetime.datetime.now(jst).hour
        if 0 < now_hour < 9 or 22 < now_hour:
            return
        warning_cold(request_json['temperature'])
        warning_hot(request_json['temperature'])

        return 'OK {}'.format(dt_now_iso)

    return 'NG {}'.format(dt_now_iso)
