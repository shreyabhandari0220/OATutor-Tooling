import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import threading
import time

import slack
import os
from pathlib import Path
from dotenv import load_dotenv

def ignore_first_call(fn):
    called = False

    def wrapper(*args, **kwargs):
        nonlocal called
        if called:
            return fn(*args, **kwargs)
        else:
            called = True
            return None

    return wrapper

@ignore_first_call
def on_snapshot(col_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == 'ADDED':
            doc = change.document.to_dict()
            problem_id = doc["problemID"]
            feedback = doc["feedback"]

            # Notify with slackbot
            alert_msg = f"New feedback:\n {problem_id}: {feedback}"
            client.chat_postMessage(channel=channel, text=alert_msg)


if __name__ == '__main__':
    cred = credentials.Certificate('./oatutor-firebase-adminsdk.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    col_query = db.collection(u'feedbacks')

    # Create an Event for notifying main thread.
    delete_done = threading.Event()

    # Watch the collection query
    query_watch = col_query.on_snapshot(on_snapshot)

    # Slockbot usage
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    # member_id = "U01GFFXHFK9"
    member_id = "U02DJM2RY66"
    client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
    ret = client.conversations_open(users=member_id)
    channel = ret["channel"]["id"]
    
    while True:
        time.sleep(2)