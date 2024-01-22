import os
import re
#from search_with_slack_api import main as search_with_slack_api
from chatgpt import main as chatgpt

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import threading

# Install the Slack app and get xoxb- token in advance
app = App(
    token=os.environ["SLACK_BOT_TOKEN"]
)


def ask_chatgpt(text, user_id, channel_id, thread_ts=None):
    # Remove any @mentions from the query
    text = re.sub(r'<@\w+>', '', text)

    # Send a message to indicate that GPT-4 is working on the request and capture the timestamp
    status_message_response = app.client.chat_postMessage(
        channel=channel_id,
        text=f"Let me ask GPT-4...",
        thread_ts=thread_ts
    )
    status_message_ts = status_message_response['ts']  # Capture the timestamp of the status message

    # Create a worker thread to perform the search and send the results
    def worker():
        response = chatgpt(text)
        # Post the GPT-4 response
        app.client.chat_postMessage(
            channel=channel_id,
            text="Here is GPT-4's response:\n" + response,
            thread_ts=thread_ts
        )
        # Delete the "Let me ask GPT-4..." status message
        app.client.chat_delete(
            channel=channel_id,
            ts=status_message_ts
        )

    # Start the worker thread
    thread = threading.Thread(target=worker)
    thread.start()
    

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)
    # Extract the event object from the body
    event = body["event"]
    # Get the user ID of the sender
    user_id = event["user"]
    # Get the text of the message
    text = event["text"]
    # Get the channel ID of the message
    channel_id = event["channel"]
    # Get the timestamp of the message
    thread_ts = event.get("ts")

    ask_chatgpt(text, user_id, channel_id, thread_ts)
        

@app.event("app_mention")
def handle_app_mention_events(body, logger):
    logger.info(body)
    # Extract the event object from the body
    event = body["event"]
    # Get the user ID of the sender
    user_id = event["user"]
    # Get the text of the message
    text = event["text"]
    # Get the channel ID of the message
    channel_id = event["channel"]
    # Get the timestamp of the message
    thread_ts = event.get("ts")

    ask_chatgpt(text, channel_id, channel_id, thread_ts)
  

# Listen for a "hello" message and respond with a greeting
@app.message("hello")
def say_hello(ack, logger, message):
    logger.info("Got hello message")
    print("Got hello message")
    user = message["user"]
    # Acknowledge the message request
    ack()
    # Send a greeting message as a direct message to the user
    app.client.chat_postMessage(channel=f"@{user}", text=f"Hello <@{user}>!")


@app.event("app_home_opened")
def app_home_opened(ack, event, logger):
    # Acknowledge the event request
    ack()
    
    # Log the event data
    logger.info(event)
    
    # Do something with the event data
    # For example, send a message to the user who opened the app home
    user_id = event["user"]
    response = app.client.chat_postMessage(
        channel=user_id,
        text=f"Hello! Welcome to my Slack app. What can I help you with today?"
    )
    logger.info(response)


if __name__ == "__main__":
    # Turn on INFO logging to see what's happening
    import logging
    logging.basicConfig(level=logging.INFO)
    # Start the app
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
  