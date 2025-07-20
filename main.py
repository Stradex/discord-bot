import threading
import asyncio
import queue
import discord
import irc.client
from dotenv import load_dotenv
import os

load_dotenv()
IRC_CHANNEL = os.getenv("IRC_CHANNEL")
IRC_SERVER = os.getenv("IRC_SERVER")
IRC_PORT = int(os.getenv("IRC_PORT"))
IRC_BOT_NAME = os.getenv("IRC_BOT_NAME")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

message_queue = queue.Queue()

def irc_bot(message_queue):
  client = irc.client.Reactor()

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
    user = event.source.nick
    text = event.arguments[0]
    print(f"[IRC] <{user}> {text}")
    message_queue.put(("irc_to_discord", f"<{user}> {text}"))

  def send_from_discord():
    while True:
      try:
        msg_type, msg = message_queue.get(block=True)
        if msg_type == "discord_to_irc":
          client.connections[0].privmsg(IRC_CHANNEL, msg)
      except Exception as e:
        print("Error sending to IRC:", e)

  try:
    c = client.server().connect(IRC_SERVER, IRC_PORT, IRC_BOT_NAME)
  except irc.client.ServerConnectionError:
    print("Connection failed.")
    return

  c.add_global_handler("welcome", on_connect)
  c.add_global_handler("join", on_join)
  c.add_global_handler("invite", on_invite)
  c.add_global_handler("pubmsg", on_pubmsg)

  threading.Thread(target=send_from_discord, daemon=True).start()

  client.process_forever()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
discord_client = discord.Client(intents=intents)
channel = None

@discord_client.event
async def on_ready():
  global channel
  print(f"Logged in as {discord_client.user}!")
  channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
  print(channel)
  # List all channels id and servers ids to help debug
  for guild in discord_client.guilds:  # all servers the bot is in
    print(f"Guild: {guild.name} (ID: {guild.id})")
    for server_channel in guild.channels:
      print(f"  Channel: {server_channel.name} (ID: {server_channel.id}) - Type: {server_channel.type}")

@discord_client.event
async def on_message(message):
  if message.author == discord_client.user:
    return
  print(f"[DISCORD] <{message.author}> {message.content}")
  message_queue.put(("discord_to_irc", f"<{message.author}> {message.content}"))

def send_from_irc():
  global channel
  while True:
    try:
      msg_type, msg = message_queue.get(block=True)
      if msg_type == "irc_to_discord":
        if channel:
          asyncio.run_coroutine_threadsafe(channel.send(msg), discord_client.loop)
    except Exception as e:
      print("Error sending to Discord:", e)



if __name__ == "__main__":
  irc_thread = threading.Thread(target=irc_bot, args=(message_queue,))
  irc_thread.start()
  threading.Thread(target=send_from_irc, daemon=True).start()
  discord_client.run(DISCORD_BOT_TOKEN)
