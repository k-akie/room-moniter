import datetime
import os

import functions_framework
from google.cloud import bigquery
from slack_sdk.web import WebClient

jst = datetime.timezone(datetime.timedelta(hours=9), "JST")


def send_slack(slack_api_token, channel, data):
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

    message = f"{greet}\r{data}"

    client = WebClient(token=slack_api_token)
    response = client.chat_postMessage(text=message, channel=channel)
    print(response)


def search_bq(table_id):
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
        createdAt = row.createdAt.astimezone(jst).strftime("%Y/%m/%d %H:%M")
        float_format = "6.1f"
        return f"""
> *{createdAt}*
> 室温    {format(row.temperature, float_format)} ℃
> 湿度    {format(row.humidity, float_format)} %
> 気圧    {format(row.pressure, float_format)} hPa
> 気体抵抗 {format(row.gas_resistance, float_format)} KOhms
                """
    return ""


@functions_framework.http
def check_room(request):
    request_json = request.get_json(silent=True)

    if request_json and 'channel' in request_json:
        channel = request_json['channel']
        table_id = os.environ.get('BIGQUERY_TABLE_ID', 'Specified environment variable is not set.')
        slack_api_token = os.environ.get('SLACK_API_TOKEN', 'Specified environment variable is not set.')

        result = search_bq(table_id)
        send_slack(slack_api_token, channel, result)
        return 'OK'

    return 'NG'
