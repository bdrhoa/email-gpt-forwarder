# Email GPT Forwarder

This application monitors an email inbox for new messages, processes them through ChatGPT, and automatically sends back the responses. It handles both email body content and attachments.

## Features

- Monitors email inbox for new messages
- Processes email content and attachments through ChatGPT
- Automatically sends responses back to the sender
- Supports text attachments
- Configurable check interval
- Secure credential management through environment variables

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

### Email Configuration

For Gmail:
1. Enable 2-factor authentication
2. Generate an App Password
3. Use your email address and the generated App Password in the `.env` file

### OpenAI Configuration

1. Get your OpenAI API key from https://platform.openai.com/
2. Add it to the `.env` file

## Running the Application

```bash
python main.py
```

The application will continuously monitor your inbox for new emails and process them automatically.

## Security Notes

- Never commit your `.env` file
- Use App Passwords instead of your main email password
- Keep your OpenAI API key secure

## Limitations

- Currently supports text-based attachments only
- Requires constant internet connection
- Processes one email at a time
