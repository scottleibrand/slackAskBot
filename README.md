# slackAskBot
slackAskBot is a Slack bot that integrates with OpenAI's GPT-4 to provide users with an interactive Q&A experience directly within Slack. Users can ask questions, and the bot, utilizing the power of GPT-4, will provide informative and contextually relevant answers.
## Features
- **Interactive Q&A**: Engage with the bot by asking questions in natural language.
- **Threaded Conversations**: The bot understands and maintains conversation context within Slack threads.
- **Asynchronous Processing**: Uses threading to handle API calls to GPT-4 without blocking Slack interactions.
- **Customizable**: Easy to extend and customize for different use cases or to add additional features.
## Prerequisites
Before you can run slackAskBot, you need to have the following:
- A Slack workspace where you have permissions to install apps.
- Slack API tokens (Bot User OAuth Token and App-Level Token).
- An OpenAI API key with access to GPT-4.
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
## Usage
To start the bot, run the following command:

   python slackAskBot.py

Once the bot is running, you can interact with it in your Slack workspace by sending direct messages or mentioning the bot in channels where it has been invited.
## Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.
## License
Distributed under the MIT License. See LICENSE for more information.
