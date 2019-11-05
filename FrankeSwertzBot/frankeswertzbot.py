import slack
from flask import Flask, request, Response
import spreadsheet
from apscheduler.schedulers.background import BackgroundScheduler

with open('bot_OAuth_token.txt') as input_file:
    token = input_file.read().strip()
client = slack.WebClient(token=token)
app = Flask(__name__)

with open('webtoken_secret.txt') as input_file:
    secret = input_file.read().strip()



@app.route('/slack', methods=['POST'])
def schedule_request():
    # Receives post requests from / commands. Parse the commands and print something
    if request.form.get('token') == secret:
        channel = request.form.get('channel_name')
        username = request.form.get('user_name')
#        text = request.form.get('text')

        frankeswertzsheet = spreadsheet.FrankeSwertzSheet()
        text = frankeswertzsheet.get_next_meeting()

        if channel == 'directmessage':
            response = client.chat_postMessage(
                channel='@'+username,
                text=text)
        else:
            response = client.chat_postMessage(
                channel=channel,
                text=text)
        assert response["ok"]
    return Response(), 200

@app.route('/slap', methods=['POST'])
def slap():
    # Receives post requests from / commands. Parse the commands and print something
    if request.form.get('token') == secret:
        channel = request.form.get('channel_name')
        username = request.form.get('user_name')
        text = request.form.get('text')
        if len(text.strip()) == 0:
            message =  f'<@{username}> slaps no one around a bit with a large trout'

        elif text.startswith('@'):
            text = text.replace('@','')
            message = f'<@{username}> slaps <@{text}> around a bit with a large trout'
        else:
            message = f'<@{username}> slaps '+text+' around a bit with a large trout'
        if channel == 'directmessage':
            response = client.chat_postMessage(
                channel='@'+username,
                text=message)
        else:
            pass
            response = client.chat_postMessage(
                channel=channel,
                text=message)
        assert response["ok"]
    return Response(), 200



def send_schedule_reminder():
    frankeswertzsheet = spreadsheet.FrankeSwertzSheet()
    text = 'Weekly reminder:\n'+frankeswertzsheet.get_next_meeting()
    text += '\nHave a great weekend!'
    response = client.chat_postMessage(
        channel="frankeswertz_general",
        text=text)
    assert response["ok"]
    return Response(), 200


scheduler = BackgroundScheduler()
job = scheduler.add_job(send_schedule_reminder, 'cron', day_of_week='fri', hour=10)
scheduler.start()
if __name__ == "__main__":
    app.run(debug=True)
