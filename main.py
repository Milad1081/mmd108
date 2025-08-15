import os
import time
from datetime import datetime
import requests
from telegram import Bot

# ====== Config via Environment Variables ======
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")  # e.g. D56NsnrP8CyfhS3jvZR2NEywD8Fxnx69Q6fZrz5cpump
NETWORK = os.getenv("NETWORK", "SOL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # e.g. @your_channel_name
INTERVAL_SECONDS = int(os.getenv("INTERVAL_SECONDS", "300"))  # default 5 minutes
RUN_ONCE = os.getenv("RUN_ONCE", "0") == "1"

TOKEN_NAME = os.getenv("TOKEN_NAME", "BANGER COIN")
TOKEN_SYMBOL = os.getenv("TOKEN_SYMBOL", "BANGER")

assert TOKEN_ADDRESS, "TOKEN_ADDRESS env var is required"
assert TELEGRAM_TOKEN, "TELEGRAM_TOKEN env var is required"
assert TELEGRAM_CHAT_ID, "TELEGRAM_CHAT_ID env var is required"

bot = Bot(token=TELEGRAM_TOKEN)

def _fmt_compact(n: float) -> str:
    try:
        n = float(n)
    except Exception:
        return "?"
    absn = abs(n)
    if absn >= 1_000_000_000:
        return f"${n/1_000_000_000:.1f}B"
    if absn >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if absn >= 1_000:
        return f"${n/1_000:.1f}K"
    return f"${n:.0f}"

def _choose_best_pair(pairs):
    # pick the pair with the highest USD liquidity (fallback: first)
    best = None
    best_liq = -1
    for p in pairs:
        liq = None
        try:
            liq = float(p.get("liquidity", {}).get("usd", 0) or 0)
        except Exception:
            liq = 0
        if liq > best_liq:
            best = p
            best_liq = liq
    return best or (pairs[0] if pairs else None)

def fetch_token_snapshot():
    url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADDRESS}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    pairs = data.get("pairs", [])
    if not pairs:
        return None
    p = _choose_best_pair(pairs)

    # Price and changes
    price_usd = float(p.get("priceUsd", 0) or 0)
    price_change = p.get("priceChange", {}) or {}
    ch_5m = float(price_change.get("m5", 0) or 0)
    ch_1h = float(price_change.get("h1", 0) or 0)
    ch_6h = float(price_change.get("h6", 0) or 0)
    ch_24h = float(price_change.get("h24", 0) or 0)

    # FDV is the closest to market cap on new tokens
    mc = float(p.get("fdv", 0) or 0)
    vol = p.get("volume", {}) or {}
    vol_h24 = float(vol.get("h24", 0) or 0)

    liq = p.get("liquidity", {}) or {}
    liq_usd = float(liq.get("usd", 0) or 0)

    # ATH approximation: not provided directly; we can use highest fdv over time if available.
    # Dexscreener "ath" may not be in this endpoint; so we omit or mark N/A.
    ath_note = "N/A"

    buyers = p.get("txns", {}).get("h1", {}).get("buys") if p.get("txns") else None
    sellers = p.get("txns", {}).get("h1", {}).get("sells") if p.get("txns") else None

    # Pair info
    dex_id = p.get("dexId", "?")
    base_token = p.get("baseToken", {}) or {}
    quote_token = p.get("quoteToken", {}) or {}
    pair_url = p.get("url", "")  # not posted to Telegram to avoid link clutter

    snapshot = {
        "price_usd": price_usd,
        "changes": {"5m": ch_5m, "1h": ch_1h, "6h": ch_6h, "24h": ch_24h},
        "market_cap": mc,
        "volume_24h": vol_h24,
        "liquidity_usd": liq_usd,
        "buyers_1h": buyers,
        "sellers_1h": sellers,
        "dex": dex_id,
        "base": base_token.get("symbol") or TOKEN_SYMBOL,
        "quote": quote_token.get("symbol") or "?",
        "ath": ath_note,
    }
    return snapshot

def build_message(snap: dict) -> str:
    price = snap["price_usd"]
    ch1h = snap["changes"]["1h"]
    time_str = datetime.utcnow().strftime("%H:%M:%S UTC")
    buyers = snap.get("buyers_1h")
    sellers = snap.get("sellers_1h")

    # Build the message similar to the style provided
    lines = []
    lines.append(f"**{TOKEN_NAME} ({TOKEN_SYMBOL})**")
    lines.append(f"├ `{TOKEN_ADDRESS}`")
    lines.append(f"└ #{NETWORK} | 🌱 Live")
    lines.append(f"📊 **Token Stats**")
    lines.append(f"├ USD: **${price:.10f}** ({ch1h:+.1f}%)")
    lines.append(f"├ MC:   **{_fmt_compact(snap['market_cap'])}**")
    lines.append(f"├ Vol:  **{_fmt_compact(snap['volume_24h'])}**")
    lines.append(f"├ LP:   **{_fmt_compact(snap['liquidity_usd'])}**")
    lines.append(f"├ 1H:   **{ch1h:+.1f}%**")
    if buyers is not None and sellers is not None:
        lines.append(f"🅑 **{buyers}**  Ⓢ **{sellers}**")
    lines.append(f"└ Last: {time_str}")
    return "\n".join(lines)

def send_once():
    snap = fetch_token_snapshot()
    if not snap:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="❌ هیچ جفت معاملاتی برای این توکن پیدا نشد.", parse_mode="Markdown")
        return
    msg = build_message(snap)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="Markdown")

def main():
    if RUN_ONCE:
        send_once()
        return
    # loop for Railway / Render, etc.
    while True:
        try:
            send_once()
        except Exception as e:
            # Log the error to console; Telegram may fail if bot not admin, etc.
            print("Error:", e, flush=True)
        time.sleep(max(30, INTERVAL_SECONDS))

if __name__ == "__main__":
    main()
