import asyncio
import os
import sys
import threading

import discord
import requests
from discord.ext import commands
from flask import Flask
from flask_cors import CORS

TOKEN = os.getenv(
    "DISCORD_TOKEN",
    "MTI5ODY0NjAzNzYyMzQ3MjIxMQ.GG7ba4.WFzNXdKhWTABhkOvk31J_Obx0XZhqFLEQ1eSyQ",
)
SUBSCRIBER_ROLE_ID = "1293979151266742354"
SIGNALS_CHANNEL = "signals"

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "Trading Bot OK"


def get_coinbase_btc_price():
    try:
        response = requests.get(
            "https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=20
        )
        response.raise_for_status()
        data = response.json()
        return float(data["data"]["amount"])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching price: {e}")
        return None


@app.route("/test-coinbase")
def test_binance():
    response = requests.get(
        "https://api.coinbase.com/v2/prices/BTC-USD/spot", timeout=20
    )
    response.raise_for_status()
    data = response.json()
    return f"BTC price: {data}"


def format_message(action, price, take_profit, margin_percent):
    return (
        f"**🪙  Bitcoin**\n\n"
        f"📊 **Direction**: {action.upper()}\n"
        f"💥 **Leverage**: Cross 100x\n\n"
        f"🔸 **Entry Price**: ${price:.2f}\n"
        f"🔹 **Take Profit (50% ROI)**: ${take_profit:.2f}\n"
        f"(*These prices are taken from Coinbase BTC-USD*)\n\n"
        f"💼 **USE {margin_percent}% MARGIN** of your total capital ✅\n\n"
        f"⚠️ **Stop Loss**: We'll update very soon.\n\n\n"
        f"<@&{SUBSCRIBER_ROLE_ID}>"
    )


def format_stop_loss_message(action, stop_loss_price):
    if action == "b":
        return (
            f"🛑 **Stop Loss Update**\n\n"
            f"📉 Exit **if candle closes below** ${stop_loss_price:.2f} 💡\n"
            f"(*If the Stop Loss needs to trail, then we'll update.*)\n\n\n"
            f"<@&{SUBSCRIBER_ROLE_ID}>"
        )
    elif action == "s":
        return (
            f"🛑 **Stop Loss Update**\n\n"
            f"📈 Exit **if candle closes above** ${stop_loss_price:.2f} 💡\n"
            f"(*If the Stop Loss needs to trail, then we'll update.*)\n\n\n"
            f"<@&{SUBSCRIBER_ROLE_ID}>"
        )


def format_trailing_stop_loss_message(action, stop_loss_price):
    if action == "b":
        return (
            f"🛑 **New Trailing Stop Loss Update**\n\n"
            f"📉 Exit **if candle closes below** ${stop_loss_price:.2f} 💡\n"
            f"(*If the Stop Loss needs to trail, then we'll update.*)\n\n\n"
            f"<@&{SUBSCRIBER_ROLE_ID}>"
        )
    elif action == "s":
        return (
            f"🛑 **New Trailing Stop Loss Update**\n\n"
            f"📈 Exit **if candle closes above** ${stop_loss_price:.2f} 💡\n"
            f"(*If the Stop Loss needs to trail, then we'll update.*)\n\n\n"
            f"<@&{SUBSCRIBER_ROLE_ID}>"
        )


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
@commands.has_permissions(administrator=True)
async def b(ctx, margin: float):
    if ctx.channel.name != SIGNALS_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    try:
        # price = get_binance_btc_price()
        price = get_coinbase_btc_price()
        # price = 100
        take_profit = price * 1.005
        action_text = "long"

        await ctx.send(format_message(action_text, price, take_profit, margin))
    except ValueError:
        await ctx.send(
            "❌ Invalid margin. Please provide a valid number (e.g., `!b 1.5`)."
        )

    await ctx.message.delete()


@bot.command()
@commands.has_permissions(administrator=True)
async def s(ctx, margin: float):
    if ctx.channel.name != SIGNALS_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    try:
        # price = get_binance_btc_price()
        price = get_coinbase_btc_price()
        # price = 100
        take_profit = price * 0.995
        action_text = "short"

        await ctx.send(format_message(action_text, price, take_profit, margin))
    except ValueError:
        await ctx.send(
            "❌ Invalid margin. Please provide a valid number (e.g., `!s 2.0`)."
        )

    await ctx.message.delete()


# Command for setting Stop Loss
@bot.command()
@commands.has_permissions(administrator=True)
async def sl(ctx, action: str, entry_price: float, stop_loss: float = None):
    if ctx.channel.name != SIGNALS_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    if action not in ["b", "s"]:
        await ctx.send("❌ Invalid action. Use `!sl b {price}` or `!sl s {price}`.")
        return

    if stop_loss is None:
        stop_loss = 5

    stop_loss_price = (
        entry_price * (1 - stop_loss / 100)
        if action == "b"
        else entry_price * (1 + stop_loss / 100)
    )

    await ctx.send(format_stop_loss_message(action, stop_loss_price))
    await ctx.message.delete()


# Command for setting Trailing Stop Loss
@bot.command()
@commands.has_permissions(administrator=True)
async def tsl(ctx, action: str, entry_price: float, stop_loss: float = None):
    if ctx.channel.name != SIGNALS_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    if action not in ["b", "s"]:
        await ctx.send("❌ Invalid action. Use `!tsl b {price}` or `!tsl s {price}`.")
        return

    if stop_loss is None:
        stop_loss = 0

    stop_loss_price = (
        entry_price * (1 - stop_loss / 100)
        if action == "b"
        else entry_price * (1 + stop_loss / 100)
    )

    await ctx.send(format_trailing_stop_loss_message(action, stop_loss_price))
    await ctx.message.delete()


# Error handler for permissions
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), threaded=True)


def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    asyncio.run(bot.start(TOKEN))


main()
