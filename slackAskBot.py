import os
import re
import json

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
from openai import OpenAI

import threading
import subprocess

# Install the Slack app and get xoxb- token in advance
app = App(
    token=os.environ["SLACK_BOT_TOKEN"]
)

# Load the channel configuration
try:
    with open('channel_config.json', 'r') as config_file:
        channel_config = json.load(config_file)
except FileNotFoundError:
    print("channel_config.json not found. Using default configuration.")
    channel_config = {}  # Use an empty dict or a default configuration
except json.JSONDecodeError:
    print("Invalid JSON in channel_config.json. Using default configuration.")
    channel_config = {}  # Use an empty dict or a default configuration

def ask_chatgpt(text, user_id, channel_id, thread_ts=None, ts=None):
    # Remove any @mentions from the query
    text = re.sub(r'<@\w+>', '', text)

    # Fetch the thread history if thread_ts is provided
    messages = []
    if thread_ts:
        messages = fetch_conversation_history(channel_id, thread_ts)
        print(messages)

    # Determine channel or user name for settings
    channel_name = determine_channel_or_user_name(channel_id, user_id)
    print(f"Channel/user name: {channel_name}")  # Print the channel name for debugging

    # Load channel-specific settings
    system_prompt, please_wait_message, helper_program = load_channel_settings(channel_name)
    #print(f"Using system_prompt: '{system_prompt}'")
    print(f"Using please_wait_message: '{please_wait_message}' for channel/user name: {channel_name}")

    # Get the bot's user ID
    bot_user_id = app.client.auth_test()["user_id"]

    # Construct the conversation history
    conversation_history = construct_conversation_history(messages, bot_user_id, user_id, text, thread_ts, ts)

    # Send a message to indicate that GPT-4 is working on the request and capture the timestamp
    status_message_ts = post_message_to_slack(channel_id, please_wait_message, thread_ts)

    def worker():
        # Check if a helper program is specified and call it
        if helper_program:
            response = call_helper_program(helper_program, conversation_history, channel_id, thread_ts)
            print(response)
        else:
            # Generate initial response with GPT-3.5-turbo
            print(conversation_history)
            initial_response_ts = None
            try:
                initial_response = gpt(conversation_history, system_prompt, model="gpt-3.5-turbo", max_tokens=1000)
                # Post the GPT-3.5-turbo response and save its timestamp
                initial_response_ts = post_message_to_slack(channel_id, f"{initial_response}", thread_ts)
                # Append the initial GPT-3.5-turbo response to the conversation history
                conversation_history.append({"role": "assistant", "content": f"GPT-3.5 response: {initial_response}"})

                # Synthetic review process
                synthetic_review = "Let’s review the GPT-3.5 response and determine whether any corrections, clarifications, or elaborations are required. If no changes are needed, reply with 'GOOD AS-IS'; if the response only needs minor elaboration, reply with 'ADDITIONAL RESPONSE:'followed by a follow-up message with any clarifications or elaborations we want to append to the last reply. Otherwise, the reply will be completely replaced with your response. If you decide to replace your previous response, don't refer to it: it will be deleted and not visible. DO NOT make reference to 'a misunderstanding in my previous response' or similar: just write a new and better response."
                conversation_history.append({"role": "assistant", "content": synthetic_review})
            except Exception as e:
                print("Error from GPT-3.5: {e}")
            print(conversation_history)

            # Enhance response with GPT-4-Turbo
            enhanced_response = gpt(conversation_history, system_prompt, model="gpt-4-turbo-preview")
            print(enhanced_response)

            # Decide what to do based on GPT-4-Turbo's response
            if "GOOD AS-IS" in enhanced_response:
                # Do nothing, keep the initial response
                print("All good; nothing more to post")
                pass
            elif "ADDITIONAL RESPONSE:" in enhanced_response:
                # Append any clarifications or elaborations as a new message
                new_response = enhanced_response.replace("ADDITIONAL RESPONSE:", "").strip()
                print("Posting an addendum")
                post_message_to_slack(channel_id, enhanced_response, thread_ts)
            else:
                # Post the new GPT-4-Turbo response
                print("Posting full GPT-4 response")
                post_message_to_slack(channel_id, enhanced_response, thread_ts)
                # Delete the initial GPT-3.5-turbo response
                if initial_response_ts:
                    print("Deleting GPT-3.5 response")
                    delete_message_from_slack(channel_id, initial_response_ts)

        # Delete the "Please wait for GPT-4..." status message
        delete_message_from_slack(channel_id, status_message_ts)

    # Start the worker thread
    thread = threading.Thread(target=worker)
    thread.start()

def fetch_conversation_history(channel_id, thread_ts):
    try:
        history = app.client.conversations_replies(channel=channel_id, ts=thread_ts)
        return history['messages']
    except SlackApiError as e:
        print(f"Failed to fetch conversation history: {e}")
        if not handle_slack_api_error(e):
            raise
        return []

def determine_channel_or_user_name(channel_id, user_id):
    try:
        channel_info = app.client.conversations_info(channel=channel_id)
        is_direct_message = channel_info['channel'].get('is_im', False)
        if is_direct_message:
            user_info = app.client.users_info(user=user_id)
            return user_info['user']['real_name']
        else:
            return channel_info['channel']['name']
    except KeyError:
        # Fallback if 'name' or other expected keys are missing
        channel_name = "default"
    except SlackApiError as e:
        print(f"Error fetching channel or user name: {e}")
        return "default"

def load_channel_settings(channel_name):
    # Load the channel configuration
    channel_settings = channel_config.get(channel_name, {})

    # Determine the system prompt based on the channel configuration or use the top-level default
    system_prompt = channel_settings.get(
        "system_prompt",
        channel_config.get("system_prompt", "You are a helpful assistant in a Slack workspace. Please format your responses for clear display within Slack by minimizing the use of markdown-formatted **bold** text and # headers in favor of Slack-compatible formatting. You do not yet have the ability to perform any actions other than responding directly to the user. The user can DM you, @ mention you in a channel you've been added to, or reply to a thread in which you are @ mentioned.")
    )

    # Determine the custom "please_wait_message" based on the channel configuration or use the top-level default
    please_wait_message = channel_settings.get(
        "please_wait_message",
        channel_config.get("please_wait_message", "Please wait for GPT-4...")
    )

    helper_program = channel_settings.get("helper_program")

    return system_prompt, please_wait_message, helper_program

def construct_conversation_history(messages, bot_user_id, user_id, current_text, thread_ts=None, ts=None):
    conversation_history = []
    for msg in messages:
        # Skip bot's own status messages
        #if msg.get("user") == bot_user_id and "Let me ask GPT-4..." in msg.get("text", ""):
            #continue
        # Check if the message is from the original user or the bot
        role = "user" if msg.get("user") == user_id else "assistant"
        content = msg.get("text")
        if content:
            conversation_history.append({"role": role, "content": content})

    # Add the current message to the conversation history if it's not already included
    if not thread_ts or thread_ts == ts:
        conversation_history.append({"role": "user", "content": current_text})

    return conversation_history

def post_message_to_slack(channel_id, text, thread_ts=None):
    try:
        response = app.client.chat_postMessage(
            channel=channel_id,
            text=text,
            thread_ts=thread_ts
        )
        return response['ts']  # Return the timestamp of the posted message
    except Exception as e:
        print(f"Failed to post message to Slack: {e}")
        return None

def delete_message_from_slack(channel_id, ts):
    try:
        app.client.chat_delete(channel=channel_id, ts=ts)
    except Exception as e:
        print(f"Failed to delete message from Slack: {e}")

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
        post_message_to_slack(channel_id, error_message, thread_ts)
        #return None
        return error_message

def handle_slack_api_error(e):
    if e.response["error"] in ["missing_scope", "not_in_channel"]:
        print(f"Slack API error due to missing permissions: {e.response['needed']}")
        # Determine fallback behavior based on the context
        return True  # Indicate that the error was handled
    return False  # Indicate that the error was not handled and should be re-raised

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

def gpt(conversation_history, system_prompt, model="gpt-4-turbo-preview", max_tokens=3000, temperature=0):

    # Get the API key from the environment variable
    api_key = os.environ["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)

    # Define the system message using the provided system prompt
    system_message = {
        "role": "system",
        "content": system_prompt
    }

    # Prepend the system message to the conversation history
    conversation_history_with_system_message = [system_message] + conversation_history

    # Use the chat completions endpoint for chat models
    response = client.chat.completions.create(model=model,
        messages=conversation_history_with_system_message,
        max_tokens=max_tokens,
        temperature=temperature)

    # Get the answer from the response
    answer = response.choices[0].message.content

    return answer

if __name__ == "__main__":
    # Turn on INFO logging to see what's happening
    import logging
    logging.basicConfig(level=logging.INFO)
    # Start the app
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
  
