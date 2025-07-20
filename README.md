## Discord <-> IRC bridge

Small python based discord <-> IRC bridge to be able to forwards messages between a discord channel and an IRC channel

## Requirements

* Python3 + pip
* Discord BOT with Token
* IRC channel
* Invite the bot to your IRC channel.

## HOWTO

Basically you first of all will need:

1. Your own IRC channel.
2. Your own Discord bot with read/write access to the channel you wish to be sending messages from.
3. The TOKEN from that Discord BOT.

After you meet the requirements, create **.env** file at the root of this repo directory based on .env.example and complete the values with yours own.

Then just run **python3 main.py**, after it invite the bot to your IRC channel, and you are set.
