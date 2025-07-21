import threading
import asyncio
import queue
import discord
from dotenv import load_dotenv
import os
import irc3

load_dotenv()
IRC_CHANNEL = os.getenv("IRC_CHANNEL")
IRC_SERVER = os.getenv("IRC_SERVER")
IRC_PORT = int(os.getenv("IRC_PORT"))
IRC_BOT_NAME = os.getenv("IRC_BOT_NAME")
IRC_USERNAME = os.getenv("IRC_USERNAME")
IRC_PASSWORD = os.getenv("IRC_PASSWORD")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

message_queue = queue.Queue()

config = {
  'nick': IRC_BOT_NAME,
  'username': IRC_USERNAME,
  'host': IRC_SERVER,
  'port': IRC_PORT,
  'ssl': True,
  'sasl_username': IRC_USERNAME,
  'sasl_password': IRC_PASSWORD,
  'sasl_mechanism': 'PLAIN',
  'includes': [
    __name__,
    'irc3.plugins.core',
    'irc3.plugins.sasl',
  ],
  'autojoins': [],
  'verbose': True,
  'timeout': 120,
  'loop': asyncio.new_event_loop(),
}

@irc3.plugin
class IRCDiscordBot:
  def __init__(self, bot):
    self.bot = bot

  @irc3.event(r'^:\S+ INVITE (?P<botnick>\S+) :(?P<channel>\S+)$')
  def on_invite(self, botnick=None, channel=None):
    print(f"Invited to channel {channel}")
    if channel == IRC_CHANNEL:
      self.bot.join(channel)
    else:
      print(f"Bot ignored invitation from {channel}")

  @irc3.event(irc3.rfc.JOIN)
  def on_join(self, mask, channel, **kw):
    if mask.nick == self.bot.nick:
      print(f"Joined {channel}")
      self.bot.privmsg(channel, "Hello world")

  @irc3.event(irc3.rfc.PRIVMSG)
  def on_pubmsg(self, mask, event, target, data, **kwargs):
    if target.startswith('#'):
      user = mask.nick
      text = data
      print(f"[IRC] <{user}> {text}")
      message_queue.put(("irc_to_discord", f"<{user}> {text}"))

def irc_bot(message_queue):
  bot = irc3.IrcBot(**config)
#  bot = irc3.IrcBot.from_config(config)

  def send_from_discord(bot, message_queue):
    while True:
      try:
        msg_type, msg = message_queue.get(block=True)
        if msg_type == "discord_to_irc":
          bot.privmsg(IRC_CHANNEL, msg)
      except Exception as e:
        print("Error sending to IRC:", e)


  threading.Thread(target=send_from_discord, args=(bot, message_queue), daemon=True).start()
  bot.run(forever=True)

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
