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
BINANCE_API_URL = "https://fapi.binance.com/fapi/v1/ticker/price?symbol=BTCUSDT"
SIGNALS_CHANNEL = "signals"
SUBSCRIBER_ROLE_ID = "1293979151266742354"

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "Bot is running"


def get_binance_btc_price():
    response = requests.get(BINANCE_API_URL)
    data = response.json()
    return float(data["price"])


def format_message(action, price, take_profit, margin_percent):
    return (
        f"**🪙  Bitcoin**\n\n"
        f"📊 **Direction**: {action.upper()}\n"
        f"💥 **Leverage**: Cross 100x\n\n"
        f"🔸 **Entry Price**: ${price:.2f}\n"
        f"🔹 **Take Profit (50% ROI)**: ${take_profit:.2f}\n"
        f"(*These prices are taken from Binance Futures*)\n\n"
        f"💼 **USE {margin_percent}% MARGIN** of your total capital ✅\n\n"
        f"⚠️ **Stop Loss**: We'll update very soon.\n\n\n"
        f"<@&{SUBSCRIBER_ROLE_ID}>"
    )


def format_stop_loss_message(action, stop_loss_price, msg_prefix=""):
    if action == "b":
        return (
            f"🛑 **{msg_prefix}Stop Loss Update**\n\n"
            f"📉 Exit **if candle closes below** ${stop_loss_price:.2f}. 💡\n"
            f"(*If the Stop Loss needs to trail, then we'll update.*)\n\n\n"
            f"<@&{SUBSCRIBER_ROLE_ID}>"
        )
    elif action == "s":
        return (
            f"🛑 **Stop Loss Update**\n\n"
            f"📈 Exit **if candle closes above** ${stop_loss_price:.2f}. 💡\n"
            f"(*If the Stop Loss needs to trail, then we'll update.*)\n\n\n"
            f"<@&{SUBSCRIBER_ROLE_ID}>"
        )


intents = discord.Intents.default()
intents.message_content = True
# client = discord.Client(intents=intents)
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.name != SIGNALS_CHANNEL:
        return

    if not message.author.guild_permissions.administrator:
        await message.channel.send("❌ You don't have permission to use this command.")
        return

    if message.content.startswith("!b ") or message.content.startswith("!s "):
        try:
            command_parts = message.content.split()
            if len(command_parts) < 2:
                await message.channel.send(
                    "❌ Please provide a valid margin (e.g., !b 1 or !s 1.5)."
                )
                return
            margin_percent = float(command_parts[1])

            action = "long" if message.content.startswith("!b") else "short"
            price = get_binance_btc_price()
            take_profit = price * (1.005 if action == "long" else 0.995)

            await message.channel.send(
                format_message(action, price, take_profit, margin_percent)
            )

        except ValueError:
            await message.channel.send(
                "❌ Invalid margin. Please provide a valid number (e.g., !b 1 or !s 0.85)."
            )
        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")

    elif message.content.startswith("!sl "):
        try:
            command_parts = message.content.split()
            if len(command_parts) != 3 or command_parts[1] not in ["b", "s"]:
                await message.channel.send(
                    "❌ Invalid command. Use !sl b {price} for buy or !sl s {price} for sell."
                )
                return

            action = command_parts[1]
            stop_loss_price = float(command_parts[2])

            await message.channel.send(
                format_stop_loss_message(action, stop_loss_price)
            )

        except ValueError:
            await message.channel.send(
                "❌ Invalid stop loss price. Please provide a valid number (e.g., !sl b 65000)."
            )

        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")

    elif message.content.startswith("!tsl "):
        try:
            command_parts = message.content.split()
            if len(command_parts) != 3 or command_parts[1] not in ["b", "s"]:
                await message.channel.send(
                    "❌ Invalid command. Use !tsl b {price} for buy or !tsl s {price} for sell."
                )
                return

            action = command_parts[1]
            stop_loss_price = float(command_parts[2])

            await message.channel.send(
                format_stop_loss_message(action, stop_loss_price, "New Trailing ")
            )

        except ValueError:
            await message.channel.send(
                "❌ Invalid stop loss price. Please provide a valid number (e.g., !tsl b 65000)."
            )

        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), threaded=True)


def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    asyncio.run(bot.start(TOKEN))


main()
