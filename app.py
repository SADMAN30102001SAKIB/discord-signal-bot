import asyncio
import os
import sys

import aiohttp
import discord
from discord.ext import commands
from quart import Quart

app = Quart(__name__)

TOKEN = os.environ["discord_token"]
SUBSCRIBER_ROLE_ID = "1293979151266742354"
SIGNALS_CHANNEL = "signals"
TEST_CHANNEL = "test"


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@app.route("/")
def home():
    return "Trading Bot OK"


async def get_coinbase_btc_price():
    url = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data["data"]["amount"])
                else:
                    print(f"Error fetching price, status code: {response.status}")
                    return None
    except aiohttp.ClientError as e:
        print(f"Error fetching price: {e}")
        return None


@app.route("/test-coinbase")
async def test_coinbase():
    price = await get_coinbase_btc_price()
    return f"BTC price: {price}"


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


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.command()
@commands.has_permissions(administrator=True)
async def b(ctx, margin: float):
    if ctx.channel.name != SIGNALS_CHANNEL and ctx.channel.name != TEST_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    try:
        price = await get_coinbase_btc_price()
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
    if ctx.channel.name != SIGNALS_CHANNEL and ctx.channel.name != TEST_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    try:
        price = await get_coinbase_btc_price()
        take_profit = price * 0.995
        action_text = "short"

        await ctx.send(format_message(action_text, price, take_profit, margin))
    except ValueError:
        await ctx.send(
            "❌ Invalid margin. Please provide a valid number (e.g., `!s 2.0`)."
        )

    await ctx.message.delete()


@bot.command()
@commands.has_permissions(administrator=True)
async def sl(ctx, action: str, entry_price: float, stop_loss: float = 0):
    if ctx.channel.name != SIGNALS_CHANNEL and ctx.channel.name != TEST_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    if action not in ["b", "s"]:
        await ctx.send("❌ Invalid action. Use `!sl b {price}` or `!sl s {price}`.")
        return

    stop_loss_price = (
        entry_price * (1 - stop_loss / 100)
        if action == "b"
        else entry_price * (1 + stop_loss / 100)
    )

    await ctx.send(format_stop_loss_message(action, stop_loss_price))
    await ctx.message.delete()


@bot.command()
@commands.has_permissions(administrator=True)
async def tsl(ctx, action: str, entry_price: float, stop_loss: float = 0):
    if ctx.channel.name != SIGNALS_CHANNEL and ctx.channel.name != TEST_CHANNEL:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    if action not in ["b", "s"]:
        await ctx.send("❌ Invalid action. Use `!tsl b {price}` or `!tsl s {price}`.")
        return

    stop_loss_price = (
        entry_price * (1 - stop_loss / 100)
        if action == "b"
        else entry_price * (1 + stop_loss / 100)
    )

    await ctx.send(format_trailing_stop_loss_message(action, stop_loss_price))
    await ctx.message.delete()


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    bot_task = bot.start(TOKEN)
    app_task = app.run_task(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    await asyncio.gather(bot_task, app_task)


if __name__ == "__main__":
    asyncio.run(main())
