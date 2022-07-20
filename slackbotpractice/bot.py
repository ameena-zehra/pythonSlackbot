from paramiko import Channel
import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter

env_path = Path('.')/'.env'
load_dotenv(dotenv_path= env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'],'/slack/events',app)
client= slack.WebClient(token=os.environ['SLACK_TOKEN'])

BOT_ID = client.api_call("auth.test")["user_id"]

welcome_messages ={}
class WelcomeMessage:
    START_TEXT = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': (
                'Welcome to this awesome channel! \n\n'
                '*Here are the commands for Nokia Inventory where you pass the Node Name as follows:*   \n\n'
                'getStatus [NodeName] \n\n cellid [NodeName] \n\n alarms [NodeName] \n\n'
                '*Here are the commands for Ericsson Inventory where you pass the Node Name and/or Cell Name as follows:*   \n\n'
                'getStatus [NodeName] \n\n listCells [NodeName] \n\n alarms [NodeName] \n\n lock [NodeName, CellName] unlock [NodeName, CellName] \n\n'
                '*Get started by reacting to this message!*'
            )
        }
    }

    DIVIDER = {'type': 'divider'}

    def __init__(self, channel):
        self.channel = channel
        self.icon_emoji = ':robot_face:'
        self.timestamp = ''
        self.completed = False

    def get_message(self):
        return {
            'ts': self.timestamp,
            'channel': self.channel,
            'username': 'Welcome Robot!',
            'icon_emoji': self.icon_emoji,
            'blocks': [
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task()
            ]
        }

    def _get_reaction_task(self):
        checkmark = ':white_check_mark:'
        if not self.completed:
            checkmark = ':white_large_square:'

        text = f'{checkmark} *React to this message!*'

        return {'type': 'section', 'text': {'type': 'mrkdwn', 'text': text}}


def send_welcome_message(channel, user):
    if channel not in welcome_messages:
        welcome_messages[channel] = {}

    if user in welcome_messages[channel]:
        return

    welcome = WelcomeMessage(channel)
    message = welcome.get_message()
    response = client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

    welcome_messages[channel][user] = welcome


@slack_event_adapter.on('message')
def message(payload):
    print(payload)
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    if user_id!=None and BOT_ID != user_id:
        if text.lower()=='start':
            #print("start")
            send_welcome_message(f'@{user_id}', user_id)

@ slack_event_adapter.on('reaction_added')
def reaction(payload):
    event = payload.get('event', {})
    channel_id = event.get('item', {}).get('channel')
    user_id = event.get('user')

    if f'@{user_id}' not in welcome_messages:
        return

    welcome = welcome_messages[f'@{user_id}'][user_id]
    welcome.completed = True
    welcome.channel = channel_id
    message = welcome.get_message()
    updated_message = client.chat_update(**message)
    welcome.timestamp = updated_message['ts']

# NOKIA FUNCTIONS
@app.route('/getstatusNokia', methods =['POST'])
def getstatusNokia():
    nodeid = request.form['text']
    channel_id = request.form['channel_id']
    if nodeid=="":
        client.chat_postMessage(channel= channel_id, text="Please enter a node name")
        return Response(), 200
    else:
        if len(nodeid)<=6 :
            import nokia_script as nokia
            response=nokia.cellstate([nodeid])
            client.chat_postMessage(channel= channel_id, text=response)
        else:
            import nokia5g_script as nokia5g
            response=nokia5g.cellstate([nodeid])
            client.chat_postMessage(channel=channel_id, text=response)    
        return Response(), 200
@app.route('/listcellsNokia', methods =['POST'])
def listcells():
    nodeid = request.form['text']
    channel_id = request.form['channel_id']
    if nodeid=="":
        client.chat_postMessage(channel= channel_id, text="Please enter a node name")
        return Response(), 200
    else:
        if len(nodeid)<=6 :
            import nokia_script as nokia
            response=nokia.listcell([nodeid])
            client.chat_postMessage(channel= channel_id, text=response)
        else:
            import nokia5g_script as nokia5g
            response=nokia5g.listcell([nodeid])
            client.chat_postMessage(channel=channel_id, text=response)    
        return Response(), 200
@app.route('/alarmsNokia', methods =['POST'])
def alarms():
    nodeid = request.form['text']
    channel_id = request.form['channel_id']
    if nodeid=="":
        client.chat_postMessage(channel= channel_id, text="Please enter a node name")
        return Response(), 200
    else:
        if len(nodeid)<=6 :
            import nokia_script as nokia
            response=nokia.alarms([nodeid])
            client.chat_postMessage(channel= channel_id, text=response)
        else:
            import nokia5g_script as nokia5g
            response=nokia5g.alarms([nodeid])
            client.chat_postMessage(channel=channel_id, text=response)    
        return Response(), 200



# ERICSSON FUNCTIONS
@app.route('/lockEricsson', methods =['POST'])
def lockEricsson():
    input = request.form['text']
    channel_id = request.form['channel_id']
    listargs = input.split(' ')
   
    if input=="" or len(listargs)<2:
        client.chat_postMessage(channel= channel_id, text="Please enter a node name followed by a space and the cell name ")
        return Response(), 200
    else:
        nodeid = listargs[0]+"/"+listargs[1]
        import ericsson_script as ericsson
        response = ericsson.lock(nodeid)
        client.chat_postMessage(channel=channel_id, text=response)    
    return Response(), 200
@app.route('/unlockEricsson', methods =['POST'])
def unlockEricsson():
    input = request.form['text']
    channel_id = request.form['channel_id']
    listargs = input.split(' ')
   
    if input=="" or len(listargs)<2:
        client.chat_postMessage(channel= channel_id, text="Please enter a node name followed by a space and the cell name ")
        return Response(), 200
    else:
        nodeid = listargs[0]+"/"+listargs[1]
        import ericsson_script as ericsson
        response = ericsson.unlock(nodeid)
        client.chat_postMessage(channel=channel_id, text=response)    
        return Response(), 200
@app.route('/getstatusEricsson', methods =['POST'])
def getstatusEricsson():
    nodeid = request.form['text']
    channel_id = request.form['channel_id']
    if nodeid=="":
        client.chat_postMessage(channel= channel_id, text="Please enter a node name")
        return Response(), 200
    else:
        import ericsson_script as ericsson
        response = ericsson.cellstate(nodeid)
        client.chat_postMessage(channel=channel_id, text=response)    
        return Response(), 200
@app.route('/cellidEricsson', methods =['POST'])
def cellidEricsson():
    nodeid = request.form['text']
    channel_id = request.form['channel_id']
    if nodeid=="":
        client.chat_postMessage(channel= channel_id, text="Please enter a node name")
        return Response(), 200
    else:
        import ericsson_script as ericsson
        response = ericsson.cellstate(nodeid)
        client.chat_postMessage(channel=channel_id, text=response)    
        return Response(), 200
@app.route('/alarmsEricsson', methods =['POST'])
def alarmsEricsson():
    nodeid = request.form['text']
    channel_id = request.form['channel_id']
    if nodeid=="":
        client.chat_postMessage(channel= channel_id, text="Please enter a node name")
        return Response(), 200
    else:
        import ericsson_script as ericsson
        response = ericsson.alarms(nodeid)
        client.chat_postMessage(channel=channel_id, text=response)    
    return Response(), 200






if __name__ == "__main__":
    app.run(debug=True)