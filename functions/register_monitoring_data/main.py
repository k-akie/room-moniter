import datetime
import os

import functions_framework
from google.cloud import bigquery
from google.cloud import firestore


def insert_bq(dt_now_iso, request_json):
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
        return 'OK {}'.format(dt_now_iso)

    return 'NG {}'.format(dt_now_iso)
