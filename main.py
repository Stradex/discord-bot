import threading
import discord
import irc.client
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
IRC_CHANNEL = os.getenv("IRC_CHANNEL")
IRC_SERVER = os.getenv("IRC_SERVER")
IRC_PORT = int(os.getenv("IRC_PORT"))
IRC_BOT_NAME = os.getenv("IRC_BOT_NAME")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")


def irc_bot():
  def on_invite(connection, event):
    channel = event.arguments[0]
    if channel == IRC_CHANNEL:
      print(f"Invited to {IRC_CHANNEL}")
      connection.join(IRC_CHANNEL)
    else:
      print(f"Invited from a non-whitelisted channel: {channel}")

  def on_connect(connection, event):
    print("Connected to server sucessfully")

  def on_join(connection, event):
    connection.privmsg(IRC_CHANNEL, "Hello from Python IRC bot!")

  def on_pubmsg(connection, event):
    print(f"<{event.source.nick}> {event.arguments[0]}")

  client = irc.client.Reactor()
  try:
    c = client.server().connect(IRC_SERVER, IRC_PORT, IRC_BOT_NAME)
  except irc.client.ServerConnectionError:
    print("Connection failed.")
    return

  c.add_global_handler("welcome", on_connect)
  c.add_global_handler("join", on_join)
  c.add_global_handler("invite", on_invite)
  c.add_global_handler("pubmsg", on_pubmsg)

  client.process_forever()

intents = discord.Intents.default()
intents.message_content = True

discord_bot = commands.Bot(command_prefix="!", intents=intents)

@discord_bot.event
async def on_ready():
  print(f"Logged in as {discord_bot.user}!")

@discord_bot.command()
async def hello(ctx):
  await ctx.send("Hello, world!")

if __name__ == "__main__":
  irc_thread = threading.Thread(target=irc_bot)
  irc_thread.start()
  discord_bot.run(DISCORD_BOT_TOKEN)
