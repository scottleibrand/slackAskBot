import os
import re
import json
from chatgpt import main as chatgpt

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import threading
import subprocess

# Install the Slack app and get xoxb- token in advance
app = App(
    token=os.environ["SLACK_BOT_TOKEN"]
)

# Load the channel configuration
with open('channel_config.json', 'r') as config_file:
    channel_config = json.load(config_file)

def ask_chatgpt(text, user_id, channel_id, thread_ts=None, ts=None):
    # Remove any @mentions from the query
    text = re.sub(r'<@\w+>', '', text)

    # Fetch the thread history if thread_ts is provided
    messages = []
    if thread_ts:
        history = app.client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )
        messages = history['messages']

    # Retrieve the channel information
    channel_info = app.client.conversations_info(channel=channel_id)
    channel_name = channel_info['channel']['name']
    print(f"Channel name: {channel_name}")  # Print the channel name for debugging

    # Determine the system prompt and helper program based on the channel configuration
    channel_settings = channel_config.get(channel_name, {})
    system_prompt = channel_settings.get(
        "system_prompt",
        "You are a helpful assistant in a Slack workspace. Please format your responses for clear display within Slack by minimizing the use of markdown-formatted **bold** text and # headers in favor of Slack-compatible formatting. You do not yet have the ability to perform any actions other than responding directly to the user. The user can DM you, @ mention you in a channel you've been added to, or reply to a thread in which you are @ mentioned."
    )
    helper_program = channel_settings.get("helper_program")

    # Determine the custom "please wait" message based on the channel configuration
    please_wait_message = channel_config.get(channel_name, {}).get(
        "please_wait_message",
        "Please wait for GPT-4..."
    )

    # Construct the conversation history
    conversation_history = []
    bot_user_id = app.client.auth_test()["user_id"]  # Get the bot's user ID
    for msg in messages:
        # Skip bot's own status messages
        if msg.get("user") == bot_user_id and "Let me ask GPT-4..." in msg.get("text", ""):
            continue
        # Check if the message is from the original user or the bot
        role = "user" if msg.get("user") == user_id else "assistant"
        content = msg.get("text")
        if content:
            conversation_history.append({"role": role, "content": content})

    # Add the current message to the conversation history if it's not already included
    if not thread_ts or thread_ts == ts:
        conversation_history.append({"role": "user", "content": text})

    # Send a message to indicate that GPT-4 is working on the request and capture the timestamp
    status_message_response = app.client.chat_postMessage(
        channel=channel_id,
        text=please_wait_message,
        thread_ts=thread_ts
    )
    status_message_ts = status_message_response['ts']  # Capture the timestamp of the status message

    def worker():
        # Check if a helper program is specified and call it
        if helper_program:
            response = call_helper_program(helper_program, conversation_history, channel_id, thread_ts)
            print(response)
        else:
            # Include the conversation history in the request to GPT-4
            raw_response = chatgpt(conversation_history, system_prompt)
            print(f"GPT-4 response: {raw_response}")  # Debug print

            # Modify the markdown to strip out the language specifier after the triple backticks
            response = re.sub(r'```[a-zA-Z]+', '```', raw_response)

        if response:
            # Post the response
            app.client.chat_postMessage(
                channel=channel_id,
                text=response,
                thread_ts=thread_ts
            )
        # Delete the "Please wait for GPT-4..." status message
        try:
            app.client.chat_delete(
                channel=channel_id,
                ts=status_message_ts
            )
        except Exception as e:
            print(f"Failed to delete status message: {e}")  # Debug print

    # Start the worker thread
    thread = threading.Thread(target=worker)
    thread.start()
    
def call_helper_program(helper_program_path, conversation_history, channel_id, thread_ts=None):
    # Convert conversation history to a string or a format the helper program expects
    conversation_str = json.dumps(conversation_history)
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    try:
        # Pass the OPENAI_API_KEY as an argument
        result = subprocess.run([helper_program_path, conversation_str, openai_api_key], capture_output=True, text=True, check=True)
        print(result)
        return result.stdout
    except FileNotFoundError:
        error_message = "The helper program was not found."
        # Handle error: send message to Slack
    except PermissionError:
        error_message = "Permission denied for the helper program. Please check the file permissions."
        # Handle error: send message to Slack
    except subprocess.CalledProcessError as e:
        print(e)
        error_message = f"Error executing the helper program"
        # Handle error: send message to Slack
    # Send error message to Slack if any
    if error_message:
        send_message_to_slack(channel_id, error_message, thread_ts)
        #return None
        return error_message

def send_message_to_slack(channel_id, text, thread_ts=None):
    try:
        app.client.chat_postMessage(
            channel=channel_id,
            text=text,
            thread_ts=thread_ts
        )
    except Exception as e:
        print(f"Failed to send message to Slack: {e}")  # Log the error for debugging

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)
    # Extract the event object from the body
    event = body["event"]

    # Check if the event is a message sent by a user and not a bot message
    if 'subtype' not in event and 'user' in event:
        # Get the channel ID of the message
        channel_id = event["channel"]
        # Get the text of the message
        text = event["text"]
        # Get the user ID of the sender
        user_id = event["user"]
        # Get the timestamp of the message
        ts = event.get("ts")
        # Check if this is a threaded message and get the thread_ts
        thread_ts = event.get("thread_ts")

        # Check if the message is a direct message or a thread reply
        if event["channel_type"] == "im":
            ask_chatgpt(text, user_id, channel_id, ts)
        elif thread_ts and thread_ts != ts:
            # Fetch the thread history to check if the bot was mentioned in the original message
            thread_history = app.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts
            )
            messages = thread_history['messages']
            bot_user_id = app.client.auth_test()["user_id"]  # Get the bot's user ID
            if any(f"<@{bot_user_id}>" in msg.get("text", "") for msg in messages if msg.get("ts") == thread_ts):
                ask_chatgpt(text, user_id, channel_id, thread_ts, ts)
            else:
                logger.info("Ignored event: bot was not @ mentioned in the original thread message")
        else:
            logger.info("Ignored event: not a direct message or thread reply")
    else:
        logger.info("Ignored event: not a user message or has subtype")

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
    ts = event.get("ts")

    # Check if the message is part of a thread
    thread_ts = event.get("thread_ts")
    if thread_ts:
        # If it's a thread, ensure the bot was mentioned in the thread
        thread_history = app.client.conversations_replies(
            channel=channel_id,
            ts=thread_ts
        )
        messages = thread_history['messages']
        bot_user_id = app.client.auth_test()["user_id"]  # Get the bot's user ID
        if any(f"<@{bot_user_id}>" in msg.get("text", "") for msg in messages):
            ask_chatgpt(text, user_id, channel_id, thread_ts)
        else:
            logger.info("Ignored app_mention: bot was not @ mentioned in the thread")
    else:
        # If it's not a thread, respond to the @ mention
        ask_chatgpt(text, user_id, channel_id, ts)
  

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
  
