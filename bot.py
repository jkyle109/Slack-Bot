import slack
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response, render_template
from slackeventsapi import SlackEventAdapter


# Load the Token from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

PORT = int(os.environ["PATH"]) | 6969
SIGNING_SECRET = os.environ['SIGNING_SECRET']
SLACK_TOKEN = os.environ['SLACK_TOKEN']
WEBHOOK_URL = os.environ['WEBHOOK_URL']

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    SIGNING_SECRET, '/slack/events', app)

# Using WebClient in slack, there are other clients built-in as well !!
client = slack.WebClient(token=SLACK_TOKEN)

# connect the bot to the channel in Slack Channel
# client.chat_postMessage(channel='#jons-hideout', text='Ready')
test_data = {'text': 'I\'m Ready!'}
requests.post(WEBHOOK_URL, json.dumps(test_data))

BOT_ID = client.api_call('auth.test')['user_id']


message_counter = {}


@slack_event_adapter.on('message')
def message(payload):
    # print(payload)
    event = payload.get('event')
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    if BOT_ID != user_id:
        if user_id in message_counter:
            message_counter[user_id] += 1
        else:
            message_counter[user_id] = 1

        # if text[-1] == '?':
        #     client.chat_postMessage(channel=channel_id, text=text)


@app.route('/mc', methods=['POST'])
def message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    count = message_counter.get(user_id, 0)

    client.chat_postMessage(
        channel=channel_id, text=f"You have {count} message(s).")
    return Response(), 200


if __name__ == '__main__':
    app.run(debug=True, port=PORT, host="0.0.0.0")
