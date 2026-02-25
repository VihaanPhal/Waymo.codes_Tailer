# Waymo Codes Telegram Notifier

Monitors [waymo.codes](https://waymo.codes/) for new referral codes and sends them to you via Telegram.

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a name for your bot (e.g., "Waymo Code Alerts")
4. Choose a username (must end in `bot`, e.g., `waymo_code_alerts_bot`)
5. **Save the bot token** - you'll need this

### 2. Get Your Chat ID

1. Message your new bot (send any message like "hi")
2. Open this URL in your browser (replace `YOUR_BOT_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. Look for `"chat":{"id":123456789}` - that number is your **Chat ID**

### 3. Deploy to Railway

1. Push this code to a GitHub repository

2. Go to [railway.app](https://railway.app/) and sign up/login

3. Click "New Project" → "Deploy from GitHub repo"

4. Select your repository

5. Go to your project settings → Variables, and add:
   - `TELEGRAM_BOT_TOKEN` = your bot token from step 1
   - `TELEGRAM_CHAT_ID` = your chat ID from step 2

6. Railway will automatically deploy. The app runs as a worker process 24/7.

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TELEGRAM_BOT_TOKEN="your_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# Run
python main.py
```

## How It Works

- Polls waymo.codes every 2 minutes
- Detects when the displayed code changes
- Sends you a Telegram notification with the new code
- Runs continuously until stopped

## Configuration

Edit `main.py` to change:
- `POLL_INTERVAL` - How often to check (default: 120 seconds)
