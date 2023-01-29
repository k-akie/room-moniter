import functions_framework
from google.cloud import firestore


@functions_framework.cloud_event
def reset_warning(cloud_event):
    db = firestore.Client()
    latest_ref = db.collection('room-monitor').document('warning')
    latest_ref.update(
        {
            'updated': firestore.SERVER_TIMESTAMP,
            'too_cold': False,
            'too_hot': False,
        }
    )
