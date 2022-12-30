import os
from search_with_slack_api import main as search_with_slack_api

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import threading

# Install the Slack app and get xoxb- token in advance
app = App(
    token=os.environ["SLACK_BOT_TOKEN"]
)

def handle_search_request(text, user_id):
    # Send a message to indicate that the app is working on the request
    app.client.chat_postMessage(channel=user_id, text=f"{text}... Let me see what I can find...")

    # Create a worker thread to perform the search and send the results
    def worker():
        answers, permalinks, timestamps = search_with_slack_api(text)
        print(f"answers: {answers}")
        if answers is None or len(answers) == 0:
            response = "Sorry, I couldn't find any answers."
            app.client.chat_postMessage(channel=user_id, text=response)
            return
        # Interleave the answers and permalinks
        response = "Here are some answers I found:\n"
        for answer, permalink in zip(answers, permalinks):
            response += f"Based on {permalink}, it appears that: {answer}\n"
            # Send the response back to the user
            app.client.chat_postMessage(channel=user_id, text=response)
            response = ""

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

    # If the message is at least three words and ends in a question mark, call search_with_slack_api to answer it
    if len(text.split()) >= 3 and text.endswith("?"):
        handle_search_request(text, user_id)
    else:
        # Respond to the message by echoing back the text
        app.client.chat_postMessage(
            channel=event["channel"],
            text=f"You said: {text}. If you want me to search for an answer, ask a question with at least three words, ending with a question mark."
        )


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

    # If the message is at least three words and ends in a question mark, start a worker thread to search for answers
    if len(text.split()) >= 3 and text.endswith("?"):
        handle_search_request(text, channel_id)
    else:
        # Respond to the message by echoing back the text
        app.client.chat_postMessage(
            channel=event["channel"],
            text=f"You said: {text}. If you want me to search for an answer, ask a question with at least three words, ending with a question mark."
        )    

        # Start the worker thread
        thread = threading.Thread(target=worker)
        thread.start()


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
  