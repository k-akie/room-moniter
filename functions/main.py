import datetime
import os

import functions_framework
from google.cloud import bigquery


@functions_framework.http
def hello_http(request):
    """HTTP Cloud Function.
   Args:
       request (flask.Request): The request object.
       <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
   Returns:
       The response text, or any set of values that can be turned into a
       Response object using `make_response`
       <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
   """
    request_json = request.get_json(silent=True)
    dt_now_iso = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()
    print(request_json, dt_now_iso)

    rows_to_insert = [{
        'createdAt': dt_now_iso,
        'temperature': request_json['temperature'],  # 温度(*C)
        'pressure': request_json['pressure'],  # 気圧(hPa)
        'humidity': request_json['humidity'],  # 湿度(%)
        'gas_resistance': request_json['gas_resistance'],  # (KOhms)
        'elevation': request_json['elevation']  # 標高(m)
    }]

    table_id = os.environ.get('BIGQUERY_TABLE_ID', 'Specified environment variable is not set.')

    client = bigquery.Client()
    table = client.get_table(table_id)
    errors = client.insert_rows(table, rows_to_insert)
    if errors:
        print("Encountered errors while inserting rows: {}".format(errors))
        return 'NG {}'.format(dt_now_iso)

    return 'OK {}'.format(dt_now_iso)
