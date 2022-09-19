import functions_framework

from google.cloud import firestore


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
    print(request_json)

    db = firestore.Client()
    new_data = db.collection('room-monitor').document()
    result = new_data.set(
        {
            'createdAt': firestore.SERVER_TIMESTAMP,
            'temperature': request_json['temperature'],  # 温度(*C)
            'pressure': request_json['pressure'],  # 気圧(hPa)
            'humidity': request_json['humidity'],  # 湿度(%)
            'gas_resistance': request_json['gas_resistance'],  # (KOhms)
            'elevation': request_json['elevation']  # 標高(m)
        }
    )
    print(str(result.update_time))

    return 'OK {}'.format(result.update_time)
