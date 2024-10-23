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
SUBSCRIBER_ROLE_ID = "1293979151266742354"
SIGNALS_CHANNEL = "signals"

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
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


# Command for Buy or Sell signals
@bot.command()
@commands.has_permissions(administrator=True)
async def signal(ctx, action: str, margin: float):
    if ctx.channel.name != SIGNALS_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    if action not in ["b", "s"]:
        await ctx.send(
            "❌ Invalid action. Use `!signal b {margin}` or `!signal s {margin}`."
        )
        return

    try:
        price = get_binance_btc_price()
        take_profit = price * (1.005 if action == "b" else 0.995)
        action_text = "long" if action == "b" else "short"

        await ctx.send(format_message(action_text, price, take_profit, margin))
    except ValueError:
        await ctx.send(
            "❌ Invalid margin. Please provide a valid number (e.g., `!signal b 1.5`)."
        )

    await ctx.message.delete()


# Command for setting Stop Loss
@bot.command()
@commands.has_permissions(administrator=True)
async def sl(ctx, action: str, stop_loss_price: float):
    if ctx.channel.name != SIGNALS_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    if action not in ["b", "s"]:
        await ctx.send("❌ Invalid action. Use `!sl b {price}` or `!sl s {price}`.")
        return

    await ctx.send(format_stop_loss_message(action, stop_loss_price))
    await ctx.message.delete()


# Command for setting Trailing Stop Loss
@bot.command()
@commands.has_permissions(administrator=True)
async def tsl(ctx, action: str, stop_loss_price: float):
    if ctx.channel.name != SIGNALS_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    if action not in ["b", "s"]:
        await ctx.send("❌ Invalid action. Use `!tsl b {price}` or `!tsl s {price}`.")
        return

    await ctx.send(format_stop_loss_message(action, stop_loss_price, "New Trailing "))
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
