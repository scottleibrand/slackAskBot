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

1. Create the App in a Slack workspace that you have permissions to install apps on:
   - Go to [https://api.slack.com/apps](https://api.slack.com/apps)
   - Click Create New App
   - Choose From an app manifest
   - Select the workspace you want to install it to.
   - Paste in the contents of [manifest.yaml](https://github.com/scottleibrand/slackAskBot/blob/main/manifest.yaml) or [manifest.json](https://github.com/scottleibrand/slackAskBot/blob/main/manifest.json
) and hit Next.
   - Hit Create.

2. Choose an always-on computer from which to run the bot. It can be a desktop computer, a virtual machine in the cloud, or anything that will always be powered on and connected to the Internet any time anyone would want to use the Slack bot.

3. On the machine you want to run the bot, clone the [slackAskBot](https://github.com/scottleibrand/slackAskBot/) repository, and install it as described in the Installation instructions:
   ```
   git clone https://github.com/scottleibrand/slackAskBot.git
   cd slackAskBot
   pip install -r requirements.txt
   ```

4. Set the necessary environment variables:
   ```
   export SLACK_BOT_TOKEN='xoxb-your-bot-token'
   export SLACK_APP_TOKEN='xapp-your-app-token'
   export OPENAI_API_KEY='your-openai-api-key'
   ```
   Detailed instructions for how to get each of those:
   - **Slack Bot Token**:
     - Go to your Slack app's **OAuth & Permissions** section (found halfway down the left sidebar).
     - Locate the **Bot User OAuth Token** and click the **Copy** button next to it.
     - In a terminal on your computer where you're installing the bot, type `export SLACK_BOT_TOKEN=`, paste the token, and hit enter.
   - **Slack App Token**:
     - Go to your Slack app's **Basic Information** page (found at https://api.slack.com/apps).
     - Scroll down to the **App-Level Tokens** section.
     - Click on your **APP_TOKEN** and click the **Copy** button next to it.
     - In the terminal, enter `export SLACK_APP_TOKEN=`, paste the token, and hit enter.
   - **OpenAI API Key**:
     - Go to the [OpenAI API Keys](https://platform.openai.com/api-keys) page.
     - Click on **Create new secret key**.
     - Give the key a name you'll recognize later, like slackAskBot for <workspace>.
     - Click **Create secret key** and then click the **Copy** button next to the generated key.
     - In the terminal, enter `export OPENAI_API_KEY=`, paste the key, and hit enter.


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
