import slack
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter
import requests

# LOADING ENVIRONMENT
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# WEB SERVER
app = Flask(__name__)
PORT = int(os.environ.get('PORT', 6969))
HOST = os.environ.get('HOST', None)
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], '/slack/events', app)

# STORING TOKEN
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']
apiKey = os.environ['API_KEY']


@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if BOT_ID != user_id:
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
                message = json.dumps([
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
                ])
                client.chat_postMessage(
                    channel=channel_id, attachments=message)


if __name__ == "__main__":
    app.run(debug=True, port=PORT, host=HOST)
