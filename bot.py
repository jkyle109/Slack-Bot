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

PORT = int(os.environ.get('PORT', 6969))
HOST = os.environ.get('HOST', None)
SIGNING_SECRET = os.environ['SIGNING_SECRET']
SLACK_TOKEN = os.environ['SLACK_TOKEN']
WEBHOOK_URL = os.environ['WEBHOOK_URL']
apiKey = os.environ['API_KEY']

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    SIGNING_SECRET, '/slack/events', app)

# Using WebClient in slack, there are other clients built-in as well !!
client = slack.WebClient(token=SLACK_TOKEN)

# connect the bot to the channel in Slack Channel
client.chat_postMessage(channel='#jons-hideout', text="I'm Ready!")
# test_data = {'text': 'I\'m Ready!'}
# requests.post(WEBHOOK_URL, json.dumps(test_data))

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

        if text[-1] == '?':
            client.chat_postMessage(channel=channel_id, text=text)
        else:
            res = requests.get(
                'http://api.openweathermap.org/data/2.5/weather?q={}&appid={}'.format(text, apiKey))
            if res.status_code == 200:
                data = res.json()
                weather_icon = "http://openweathermap.org/img/wn/{}@2x.png".format(
                    data["weather"][0]["icon"])
                weather_des = data["weather"][0]["description"]
                temp = str(round(data["main"]["temp"] - 273.15)) + "°C"
                feels_temp = str(
                    round(data["main"]["feels_like"] - 273.15)) + "°C"
                humidity = str(data["main"]["humidity"]) + "%"
                pressure = str(data["main"]["pressure"]) + " hPa"
                city = data["name"]
                country = data["sys"]["country"]
                time = data["dt"]
                message = {
                    "channel": channel_id,
                    "attachments": [
                        {
                            "color": "#",
                            "title": "Weather in {}, {}:".format(city, country),
                            "fields": [
                                {
                                    "title": "Temperature:",
                                    "value": "It is {} and feels like {}.".format(temp, feels_temp),
                                    "short": True
                                },
                                {
                                    "title": "Description:",
                                    "value": weather_des,
                                    "short": True
                                },
                                {
                                    "title": "Humidity:",
                                    "value": humidity,
                                    "short": True
                                },
                                {
                                    "title": "Atmospheric Pressure:",
                                    "value": pressure,
                                    "short": True
                                }
                            ],
                            "thumb_url": weather_icon,
                            "footer": "OpenWeather.org",
                            "footer_icon": "https://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/icons/logo_32x32.png",
                            "ts": time,
                        }
                    ]
                }
                client.chat_postMessage(
                    channel=channel_id, attachments=message)


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
    app.run(debug=True, port=PORT, host=HOST)
