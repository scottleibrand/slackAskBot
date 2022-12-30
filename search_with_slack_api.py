import os
import sys
import json
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import openai
from openai.embeddings_utils import get_embedding, cosine_similarity
import tiktoken
import pandas as pd
import numpy as np



def main():
    botclient, userclient, channels = slack_api_setup()

    # Get the search query from the command-line argument
    if len(sys.argv) < 2:
        # Print usage help if no search query is provided
        print("Usage: python search_script.py <search_query> [num_results]")
        sys.exit(1)
    else:
        query = sys.argv[1]

    # Get the number of results to return
    if len(sys.argv) > 2:
        num_results = int(sys.argv[2])
    else:
        num_results = 1

    # Call the search function to get the results
    results = search(query, userclient, channels, num_results)

    # For each result, get the surrounding context
    results_context = []
    for result in results:
        # Check that result is not None
        if result is None or result == []:
            continue
        #print(result)
        #print(result[0]['text'])
        result_context = get_message_context(result, channels, userclient)
        results_context.append(result_context)
    
    # Get embeddings for each result and its surrounding context
    contexts = []
    embeddings = []
    for result in results_context:
        for context in result:
            context_string = ''
            for message in context:
                #print(message['text'])
                context_string += message['text'] + "\n"
            #print(context_string)

            if context_string == '':
                continue
            embedding = openai.embeddings_utils.get_embedding(
                context_string,
                engine="text-embedding-ada-002"
            )
            contexts.append(context_string)
            embeddings.append(embedding)
            #print(len(embeddings))

    # Search the embeddings for the search term
    df = semantic_search(contexts, embeddings, query)
    contextualize_results(df, query)

def semantic_search(contexts, embeddings, query):
    # Get the embedding for the search term
    query_embedding = openai.embeddings_utils.get_embedding(
        query,
        engine="text-embedding-ada-002"
    )

    n = 2

    # Create a dictionary containing results and embeddings
    data = {}
    # Print length of contexts and embeddings
    print("Length of contexts: " + str(len(contexts)))
    print("Length of embeddings: " + str(len(embeddings)))
    data['results'] = contexts
    data['embeddings'] = embeddings
    

    # load the data from the embeddings variable into a pandas dataframe
    df = pd.DataFrame(data)
    print(df.head())
    #df = pd.read_json(embeddings)
    #df["ada_search"] = df.ada_search.apply(eval).apply(np.array)
    df.embeddings.apply(np.array)

    embedding = get_embedding(
        query,
        engine="text-embedding-ada-002"
    )
    df["similarities"] = df.embeddings.apply(lambda x: cosine_similarity(x, embedding))
    print(df.sort_values("similarities", ascending=False).head(n))

    return df

def contextualize_results(df, query):
    
    n=2

    res = (
        df.sort_values("similarities", ascending=False)
        .head(n)
        .results
        # Get all the elements of the list
        .apply(lambda x: x)
    )

    #print(res)
    #return res
    #if pprint:
    for result in res:

        results_string = json.dumps(result)
        
        # Get the token length of the string
        enc = tiktoken.get_encoding("gpt2")
        tokens = enc.encode(results_string)
        token_count = len(tokens)
        # print the length of the string in characters and tokens
        #print("String length: " + str(len(results_string)) + " characters, "Token count: " + str(token_count))
        print(f"String length: {len(results_string)} characters, Token count: {token_count}")

        

        prompt = "Given the following context:\n" + results_string + \
            "\nIf the context is not relevant to the question, reply with 'The context is not relevant to the question.'\n" +\
            "Question: " + query + "\nOtherwise, answer the question and provide a quote or summarization from the context to support your answer."
        #print(prompt)
        #return
        answer = ask_gpt(results_string, prompt)
        print(answer)    

def search(query, userclient, channels, num_results):
    search_terms_tried = []
    results = []
    # As long as there are no results, keep trying to search until we have tried num_results times
    search_tries = 0
    while len(results) == 0 or results[len(results)-1] == [] and search_tries < num_results:
        # Call the get_search_terms function to get the search terms
        if len(search_terms_tried) > 0:
            print ("No results found. Trying again with more general search terms.")
            search_terms = get_search_terms(query, search_terms_tried)
        else:
            search_terms = get_search_terms(query)
        print(search_terms)
        # if search_terms has multiple lines that contain search text, search for each line
        number_of_results = 0
        if search_terms.count('\n') > 0:
            for term in search_terms.split('\n'):
                if term:
                    result = perform_search(term, userclient, num_results)
                    results.append(result)
                    # Calculate the total number of results across all result fields in results
                    number_of_results += len(result)

                    print(f"Found {len(result)} results for {term}, for a total of {number_of_results} results so far.")
        else:
            messages = perform_search(search_terms, userclient, num_results)
            results.append(messages)

        #print(results[0])
        
        search_terms_tried.append(search_terms)
        search_tries += 1
        print(search_terms_tried)
    return results

def get_message_context(messages, channels, userclient):
    # Create a list to store the messages' context
    messages_context = []
    # Iterate over the messages
    for message in messages:
        # Look up the message channel in the channels list
        channel = next((channel for channel in channels if channel["id"] == message["channel"]["id"]), None)
        if channel is None:
            continue
        # Print the channel name and message text
        #print(message)
        #print("#" + channel["name"], message["text"])
        #print(message['text'])

        # Retrieve all other messages in the channel up to 1 hour before and 24h after the current message
        date = int(message["ts"].split(".")[0])
        #print(message["ts"])
        lookback = 3600 # 1 hour in seconds
        lookahead = 86400 # 24 hours in seconds
        response = userclient.conversations_history(channel=channel["id"], oldest=date-lookback, latest=date+lookahead)
        # append the messages to the messages_context list
        messages_context.append(response["messages"])
        #messages_context = response["messages"]
        #print(messages_context)
        # Print the messages in the channel on the same date
        #for message in messages_context:
            #print(message["text"])
        

    return messages_context

def slack_api_setup():
    # Set the SLACK_APP_TOKEN and SLACK_BOT_TOKEN environment variables
    # to the app token and bot token, respectively
    #app_token = os.environ["SLACK_APP_TOKEN"]
    bot_token = os.environ["SLACK_BOT_TOKEN"]
    user_token = os.environ["SLACK_USER_TOKEN"]

    botclient = WebClient(token=bot_token)
    userclient = WebClient(token=user_token)

    try:
        # Call the conversations.list method using the WebClient
        response = botclient.conversations_list()
        channels = response["channels"]

        # Print the names of all channels in the team
        #for channel in channels:
            #print(channel["name"])

    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        # (caused by an error returned by the Slack API)
        print("Error: {}".format(e))

    return botclient, userclient, channels
    

def get_search_terms(query, previous_search_terms=None):
    
    # Check whether the query is a question or search terms
    if len(query.split()) >= 3 and query.endswith("?"):
        if previous_search_terms is not None:
            # If the previous search terms are not None, use them as a prompt
            prompt = f"Please generate one or more Slack search string(s) for the following question: {query}.\n \
                Please return each search string on a separate line, without quotes or other punctuation.\n \
                You already tried:\n{previous_search_terms}\n \
                and that returned no results. Please try a more general search that will return more results.\n"
        else:
            # Use GPT to generate good Slack search terms for the question
            prompt = f"Please generate one or more Slack search string(s) for the following question: {query}.\n \
                Please return each search string on a separate line, without quotes or other punctuation.\n"
        search_terms = ask_gpt(text=query, prompt=prompt)
        print(f"Search terms: {search_terms}")
        return search_terms
    else:
        return query

def ask_gpt(text, prompt, model="text-davinci-003", max_tokens=3000):
    # Get the API key from the environment variable
    api_key = os.environ["OPENAI_API_KEY"]
    openai.api_key = api_key

    # Set the model to use, if not specified
    if model is None:
        model = "text-davinci-003"

    # Set the temperature for sampling
    temperature = 0

    # Set the max token count for the summary
    if model == "text-davinci-003":
        max_tokens = 1000
    else:
        max_tokens = 500

    # Generate completions
    completions = openai.Completion.create(
        engine=model,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )

    # Get the summary from the first completion
    summary = completions.choices[0].text

    return summary


def perform_search(query, userclient, num_results):
    # Search for messages containing the query
    try:
        # Call the search.messages method using the WebClient



        response = userclient.search_messages(
            query=query,
            sort="timestamp",
            sort_dir="asc",
            #channel=channel,
            count=num_results
        )

        print(f"Search results for query: {query}, max results: {num_results}")
        # Print the results
        #print(response["messages"])
        messages = response["messages"]["matches"]
        print(f"Found {len(messages)} results for query: {query}.")
        return messages
        #print(messages)
        #for message in messages:
            #print(message["text"])

    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        # (caused by an error returned by the Slack API)
        print("Error: {}".format(e))

if __name__ == "__main__":
    main()
