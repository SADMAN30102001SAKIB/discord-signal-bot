import asyncio
import sys

import aiohttp
import discord

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TOKEN = ""
SIGNALS_CHANNEL = "signals"
TEST_CHANNEL = "test"
ALERTS_CHANNEL = "alerts"
SUBSCRIBER_ROLE_ID = "1293979151266742354"


async def get_coinbase_eth_price():
    url = "https://api.coinbase.com/v2/prices/ETH-USD/spot"
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


def format_message(action, price, take_profit, margin_percent, roi, reEntry=""):
    if reEntry == "ReEntry":
        return (
            f"**🔷  Ethereum**\n\n"
            f"📊 **Direction**: {action.upper()}\n"
            f"💥 **Leverage**: Cross 50x\n\n"
            f"⚠️ **Note**: *This is a 2nd entry!*\n"
            f"🔸 **2nd Entry Price**: ${price:.2f}\n"
            f"🔹 **Take Profit ({roi*50}% ROI)**: ${take_profit:.2f}\n"
            f"(*These prices are taken from Coinbase ETH-USD*)\n\n"
            f"💼 **USE {margin_percent}% MARGIN** of your total capital ✅\n\n"
            f"⚠️ **Stop Loss**: *We'll update very soon*.\n\n\n"
            f"<@&{SUBSCRIBER_ROLE_ID}>"
        )
    return (
        f"**🔷  Ethereum**\n\n"
        f"📊 **Direction**: {action.upper()}\n"
        f"💥 **Leverage**: Cross 50x\n\n"
        f"🔸 **Entry Price**: ${price:.2f}\n"
        f"🔹 **Take Profit ({roi*50}% ROI)**: ${take_profit:.2f}\n"
        f"(*These prices are taken from Coinbase ETH-USD*)\n\n"
        f"💼 **USE {margin_percent}% MARGIN** of your total capital ✅\n"
        f"⚠️ **Note**: *If we need a 2nd entry, then we'll update.*\n\n"
        f"⚠️ **Stop Loss**: *We'll update very soon*.\n\n\n"
        f"<@&{SUBSCRIBER_ROLE_ID}>"
    )


def format_alert_message(action, margin_percent, price, reEntry=""):
    if price == None:
        msg = (
            f"<@&{SUBSCRIBER_ROLE_ID}> **Heads-Up!**\n"
            f"**🔔 Potential {reEntry}Signal - Ethereum**\n\n"
            f"📊 **Direction**: {action.upper()}\n"
            f"💥 **Leverage**: Cross 50x\n\n"
            f"💼 **Prepare to USE {margin_percent}% MARGIN** if the official signal confirms ✅\n\n"
            f"⚠️ **Note**: *This is just a prediction!*\nSo, prepare yourself & have patience. An official signal might or might not come."
        )
    else:
        msg = (
            f"<@&{SUBSCRIBER_ROLE_ID}> **Heads-Up!**\n"
            f"**🔔 Potential {reEntry}Signal - Ethereum**\n\n"
            f"📊 **Direction**: {action.upper()}\n"
            f"💥 **Leverage**: Cross 50x\n\n"
            f"🔸 **Possible Entry Price**: ${price:.2f}\n"
            f"(*This price is subject to change and taken from Coinbase ETH-USD*)\n\n"
            f"💼 **Prepare to USE {margin_percent}% MARGIN** if the official signal confirms ✅\n\n"
            f"⚠️ **Note**: *This is just a prediction!*\nSo, prepare yourself & have patience. An official signal might or might not come."
        )
    return msg


def format_stop_loss_message(action, stop_loss_price, msg_prefix=""):
    if action == "b":
        return (
            f"🛑 **{msg_prefix}Stop Loss Update**\n\n"
            f"📉 Exit **if candle closes below** ${stop_loss_price:.2f} on the 5-minute candlestick chart. 💡\n"
            f"(*If the Stop Loss needs to trail or an early exit is required, then we'll notify.*)\n\n\n"
            f"<@&{SUBSCRIBER_ROLE_ID}>"
        )
    elif action == "s":
        return (
            f"🛑 **{msg_prefix}Stop Loss Update**\n\n"
            f"📈 Exit **if candle closes above** ${stop_loss_price:.2f} on the 5-minute candlestick chart. 💡\n"
            f"(*If the Stop Loss needs to trail or an early exit is required, then we'll notify.*)\n\n\n"
            f"<@&{SUBSCRIBER_ROLE_ID}>"
        )


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if (
        message.channel.name != SIGNALS_CHANNEL
        and message.channel.name != TEST_CHANNEL
        and message.channel.name != ALERTS_CHANNEL
    ):
        return

    if not message.author.guild_permissions.administrator:
        await message.channel.send("❌ You don't have permission to use this command.")
        return

    if message.channel.name == ALERTS_CHANNEL and (
        message.content.startswith("!b ") or message.content.startswith("!s ")
    ):
        try:
            command_parts = message.content.split()
            if len(command_parts) < 2:
                await message.channel.send(
                    "❌ Please provide a valid margin (e.g., !b 1 or !s 1.5 70580)"
                )
                return
            margin_percent = float(command_parts[1])

            action = "long" if message.content.startswith("!b") else "short"
            price = None

            if len(command_parts) == 3:
                price = float(command_parts[2])

            await message.channel.send(
                format_alert_message(
                    action,
                    margin_percent,
                    price,
                )
            )

        except ValueError:
            await message.channel.send(
                "❌ Invalid margin. Please provide a valid number (e.g., !b 1 68456 or !s 0.85)."
            )
        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")

    elif message.channel.name == ALERTS_CHANNEL and (
        message.content.startswith("!rb ") or message.content.startswith("!rs ")
    ):
        try:
            command_parts = message.content.split()
            if len(command_parts) != 2:
                await message.channel.send(
                    "❌ Please provide a valid margin (e.g., !rb 1 or !rs 0.85)"
                )
                return
            margin_percent = float(command_parts[1])

            action = "long" if message.content.startswith("!rb") else "short"
            price = None

            await message.channel.send(
                format_alert_message(
                    action,
                    margin_percent,
                    price,
                    "2nd Entry ",
                )
            )

        except ValueError:
            await message.channel.send(
                "❌ Invalid margin. Please provide a valid number (e.g., !rb 1 or !rs 0.85)."
            )
        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")

    elif message.channel.name == ALERTS_CHANNEL and message.content.startswith("!o"):
        try:
            command_parts = message.content.split()
            if len(command_parts) > 2:
                await message.channel.send(
                    "❌ Invalid command. It should be !o or !o 2"
                )
                return
            if len(command_parts) == 2:
                margin_percent = float(command_parts[1])
                await message.channel.send(
                    f"We Might Exit Now & Take a New Trade in the Opposite Direction With {margin_percent}% Margin of Our Total Capital! Be Ready for the Official Signals. <@&{SUBSCRIBER_ROLE_ID}>"
                )
            else:
                await message.channel.send(
                    f"We Might Exit Now & Take a New Trade in the Opposite Direction! Be Ready for the Official Signal. <@&{SUBSCRIBER_ROLE_ID}>"
                )

        except ValueError:
            await message.channel.send("❌ Invalid command. It should be !o or !o 2")
        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")

    elif message.channel.name == ALERTS_CHANNEL and message.content.startswith("!e"):
        try:
            await message.channel.send(
                f"We Might Exit Now! Be Ready for the Official Signal. <@&{SUBSCRIBER_ROLE_ID}>"
            )

        except ValueError:
            await message.channel.send("❌ Invalid command. It should be !e")
        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")

    elif message.content.startswith("!e"):
        try:
            command_parts = message.content.split()
            if len(command_parts) > 2:
                await message.channel.send(
                    "❌ Invalid command. It should be !e or !e .4"
                )
                return
            if len(command_parts) == 2:
                percent = float(command_parts[1])
                await message.channel.send(
                    f"Exit Now. We Took a Loss on This Trade, Reducing Our Total Capital by {percent}% <@&{SUBSCRIBER_ROLE_ID}>"
                )
            else:
                await message.channel.send(f"Exit Now <@&{SUBSCRIBER_ROLE_ID}>")

        except ValueError:
            await message.channel.send("❌ Invalid command. It should be !e")
        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")

    elif message.content.startswith("!b ") or message.content.startswith("!s "):
        try:
            command_parts = message.content.split()
            if len(command_parts) < 2:
                await message.channel.send(
                    "❌ Please provide a valid margin (e.g., !b 1 or !s 1.5 70580)"
                )
                return
            margin_percent = float(command_parts[1])

            action = "long" if message.content.startswith("!b") else "short"
            price = None
            roi = 1

            if len(command_parts) == 2:
                price = await get_coinbase_eth_price()
            elif len(command_parts) == 3:
                price = await get_coinbase_eth_price()
                roi = float(command_parts[2])
            elif len(command_parts) == 4:
                roi = float(command_parts[2])
                price = float(command_parts[3])

            if price is None:
                await message.channel.send(
                    "❌ Failed to fetch the price. Please try again later."
                )
            else:
                take_profit = price * (
                    (1 + (roi / 100)) if action == "long" else (1 - (roi / 100))
                )
                await message.channel.send(
                    format_message(action, price, take_profit, margin_percent, roi)
                )

        except ValueError:
            await message.channel.send(
                "❌ Invalid margin. Please provide a valid number (e.g., !b 1 68456 or !s 0.85)"
            )
        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")

    elif message.content.startswith("!rb ") or message.content.startswith("!rs "):
        try:
            command_parts = message.content.split()
            if len(command_parts) != 3:
                await message.channel.send(
                    "❌ Please provide a valid margin (e.g., !rb 1 70580 or !rs 1.5 70580)"
                )
                return
            margin_percent = float(command_parts[1])

            action = "long" if message.content.startswith("!rb") else "short"

            price = await get_coinbase_eth_price()
            firstEntry = float(command_parts[2])

            if price is None:
                await message.channel.send(
                    "❌ Failed to fetch the price. Please try again later."
                )
            else:
                take_profit = ((price + firstEntry) / 2) * (
                    1.01 if action == "long" else 0.99
                )
                await message.channel.send(
                    format_message(
                        action, price, take_profit, margin_percent, 1, "ReEntry"
                    )
                )

        except ValueError:
            await message.channel.send(
                "❌ Invalid margin. Please provide a valid number (e.g., !rb 1 68456 or !rs 0.85 70580)"
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
                    "❌ Invalid command. Use !sl b {price} for buy or !sl s {price} for sell"
                )
                return

            action = command_parts[1]
            stop_loss_price = float(command_parts[2])

            await message.channel.send(
                format_stop_loss_message(action, stop_loss_price)
            )

        except ValueError:
            await message.channel.send(
                "❌ Invalid stop loss price. Please provide a valid number (e.g., !sl b 65000)"
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
                    "❌ Invalid command. Use !tsl b {price} for buy or !tsl s {price} for sell"
                )
                return

            action = command_parts[1]
            stop_loss_price = float(command_parts[2])

            await message.channel.send(
                format_stop_loss_message(action, stop_loss_price, "New Trailing ")
            )

        except ValueError:
            await message.channel.send(
                "❌ Invalid stop loss price. Please provide a valid number (e.g., !tsl b 65000)"
            )

        try:
            await message.delete()
        except discord.Forbidden:
            print("Bot doesn't have permission to delete messages.")
        except discord.HTTPException:
            print("Failed to delete message due to an HTTP error.")


client.run(TOKEN)
