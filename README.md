# slackAskBot
Use GPT-3 to do semantic search over exported Slack messages to find answers to questions about previously discussed topics

slackAskBot is a project that uses natural language processing (NLP) to search through a given dataset for messages that are similar to a given search string. It uses OpenAI's text-embedding-ada-002 engine to generate embeddings for the search string and the messages in the dataset, and then uses cosine similarity to find the most similar messages. It then prints out the top n results, and uses OpenAI's text-davinci-003 engine to generate a summary of the context and answer the question.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

You will need to have Python 3 installed on your machine.

### Installing

Clone the repository to your local machine:

```
git clone https://github.com/scottleibrand/slackAskBot.git
```

Navigate to the project directory:

```
cd slackAskBot
```

## Usage


If you're a Slack workspace or org Owner/Admin, you can export your Slack history by following the steps at https://slack.com/help/articles/201658943-Export-your-workspace-data
If you're not a Slack admin, you can ask an admin to export only your Slack history.

Once you've got a Slack export, the following scripts can be used to perform all the necessary processing to filter out just the Slack messages and generate and store (as files) the semantic search embeddings required to search for the content most relevant to the search inquiry. They should be generally be used in the order listed below.

Once you've done all the initial processing on your Slack export, you can simply run `search.py everything.json "your topical inquiry or question"` and it will find the most relevant results, and ask InstructGPT to use them to summarize the context most relevant to your inquiry and answer any explicit question you asked.

### process_slack_export.py

This script processes a Slack export file and extracts the messages with "type": "message". It takes two command-line arguments: the input file path and the output file path. It reads the input file as JSON, extracts the messages, and writes them as JSON to the output file.

### extract_messages.py

This script extracts messages with "type": "message" from a JSON file and writes them to a new JSON file. It takes two command-line arguments: the input file path and the output file path. The script opens the input file and reads the JSON data. It then extracts the messages with "type": "message" and stores them in a list. It then writes them out in a compact pretty-printed format that is valid json with newlines for readability.

### combine_messages.py

This script combines multiple small files of messages into one file. It splits large files of data into smaller parts based on the number of tokens in each part. It takes in data from the 'trimmed' directory and splits it into parts with a maximum of 1000 tokens each. The parts are then written to the 'combined' directory. The script also combines multiple files into one if the total number of tokens is less than 1000. The output files are named with the start and end dates of the data they contain.

### get-all-embeddings.py

This script processes files in an input directory and gets embeddings using OpenAI Text Embedding API, writing the embeddings to an output directory. It takes an input directory and an output directory as command-line arguments and processes all the files in the input directory. For each file, it gets the embedding using the OpenAI Text Embedding API and writes the embedding to an identically named file in the output directory. If the line is longer than 8000 tokens, it will split the line into chunks of <8000 tokens and write each chunk to its own file.

### combine_into_json.py

This script combines data from two different JSON files into one output file. It takes three arguments: `data_dir`, `embeddings_dir`, and `output_file`. It iterates over the subdirectories in the `data_dir` and looks for JSON files. It then reads the data from the JSON files and checks for an embeddings file in the `embeddings_dir` with the same name. If the embeddings file is found, it is added to the data JSON. All the data is then written to the `output_file` in a pretty-printed format.


### search.py

This script searches through a given dataset for messages that are similar to a given search string. It uses OpenAI's text-embedding-ada-002 engine to generate embeddings for the search string and the messages in the dataset, and then uses cosine similarity to find the most similar messages. It then prints out the top n results, and uses OpenAI's text-davinci-003 engine to generate a summary of the context and answer the question.

## Contributing

If you would like to contribute to the project, please open a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.
