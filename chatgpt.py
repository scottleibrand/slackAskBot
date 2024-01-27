import os
import sys
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from openai import OpenAI

client = OpenAI(api_key=api_key)


def main(question):
    botclient, userclient, channels = slack_api_setup()

    print(question)

    # Directly call the OpenAI API to get the response
    response = ask_gpt(question)

    return response


def slack_api_setup():
    # Set the SLACK_APP_TOKEN and SLACK_BOT_TOKEN environment variables
    # to the app token and bot token, respectively
    #app_token = os.environ["SLACK_APP_TOKEN"]
    bot_token = os.environ["SLACK_BOT_TOKEN"]
    user_token = os.environ["SLACK_USER_TOKEN"]

    botclient = WebClient(token=bot_token)
    userclient = WebClient(token=user_token)

    try:
        # Call the conversations.list method using the WebClient, with a limit of 1000 non-archived channels
        response = botclient.conversations_list(limit=1000, exclude_archived=True)
        #response = botclient.conversations_list()
        channels = response.channels

        # Print the names of all channels in the team
        #for channel in channels:
            #print(channel["name"])

    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        # (caused by an error returned by the Slack API)
        print("Error: {}".format(e))

    return botclient, userclient, channels
    

def ask_gpt(conversation_history, model="gpt-4-1106-preview", max_tokens=3000, temperature=0):
    # Get the API key from the environment variable
    api_key = os.environ["OPENAI_API_KEY"]

    # Define the system message
    system_message = {
        "role": "system",
        "content": "You are slackAskBot, a helpful assistant in a Slack workspace. Please format your responses for clear display within Slack. You do not yet have the ability to perform any actions other than responding directly to the user. The user can DM you, @ mention you in a channel you've been added to, or reply to a thread in which you are @ mentioned."
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

    # Get the search query from the command-line argument
    if len(sys.argv) < 1:
        # Print usage help if no search query is provided
        print("Usage: python search_script.py <search_query> [num_results]")
        sys.exit(1)
    else:
        query = sys.argv[1]

    main(query)
