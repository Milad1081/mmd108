# Solana Token Telegram Bot

This bot fetches token stats from Dexscreener and posts formatted updates to a Telegram channel.

## Environment Variables
- `TELEGRAM_TOKEN` — Bot token from @BotFather
- `TELEGRAM_CHAT_ID` — e.g. `@YourChannelUsername` (bot must be an admin of the channel)
- `TOKEN_ADDRESS` — Solana token mint address
- `NETWORK` — default `SOL`
- `TOKEN_NAME` — optional display name
- `TOKEN_SYMBOL` — optional display symbol
- `INTERVAL_SECONDS` — loop interval (default 300)
- `RUN_ONCE` — set to `1` to run once and exit (used by GitHub Actions)

## Run Locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

export TELEGRAM_TOKEN=xxx
export TELEGRAM_CHAT_ID=@yourchannel
export TOKEN_ADDRESS=YourMintAddress
export NETWORK=SOL
export TOKEN_NAME="BANGER COIN"
export TOKEN_SYMBOL="BANGER"
export RUN_ONCE=1

python main.py
```

## Railway
- Connect your GitHub repo and deploy.
- Set environment variables in Railway's "Variables".
- Ensure the bot is admin of the channel.
- Leave `RUN_ONCE` unset or `0` to keep looping.
