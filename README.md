# slackAskBot

slackAskBot is a Slack bot that integrates with OpenAI's GPT models to provide users with an interactive Q&A experience directly within Slack. Leveraging the power of GPT-3.5-turbo and GPT-4, the bot offers informative, contextually relevant answers, and can execute custom functions based on user queries.

## Features

- **Interactive Q&A**: Engage with the bot by asking questions in natural language. The bot uses GPT-3.5-turbo for quick initial responses and GPT-4 for in-depth follow-ups.
- **Threaded Conversations**: Maintains conversation context within Slack threads, ensuring coherent and contextually relevant interactions.
- **Asynchronous Processing**: Utilizes threading to handle API calls and function executions without blocking Slack interactions.
- **Custom Function Calls**: Supports calling custom functions directly from within the bot's processing logic, allowing for dynamic interactions and operations.
- **Virtual Environment Support**: Executes helper programs within their own Python virtual environments, ensuring dependency isolation and reducing conflicts.
- **Customizable Settings**: Channel-specific settings can be configured, including custom prompts and messages, to tailor the bot's behavior to different Slack channels.

## Prerequisites

Before you can run slackAskBot, you need to have the following:

- A Slack workspace where you have permissions to install apps.
- Slack API tokens (Bot User OAuth Token and App-Level Token).
- An OpenAI API key with access to GPT-3.5-turbo and GPT-4 models.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/scottleibrand/slackAskBot.git
   cd slackAskBot
   ```
2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```
3. Set the necessary environment variables:
   ```
   export SLACK_BOT_TOKEN='xoxb-your-bot-token'
   export SLACK_APP_TOKEN='xapp-your-app-token'
   export OPENAI_API_KEY='your-openai-api-key'
   ```

## Configuration

- **Channel Configuration**: Customize channel-specific settings by editing `channel_config.json`.
- **Function Configuration**: Define custom functions and their helper programs in `functions.json`.

## Usage

To start the bot, run the following command:

   `python slackAskBot.py`

Once the bot is running, you can interact with it in your Slack workspace by sending direct messages or mentioning the bot in channels where it has been invited.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
