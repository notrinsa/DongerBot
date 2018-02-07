#!/usr/bin/env python

# server.address .port .pass .channel
# IRC Address Configuration
server = {
    'address': 'irc.redditairfrance.fr',
    'port': 6697,
    'pass': None,
    'channel': '#reddit'
}
donger_nick = "donger"
donger_pass = "donger"
hostnames = ["redd.it"]

# MySQL
database = {
    'name': 'donger',
    'user': 'donger',
    'pass': 'donger'
}

# super_secret_command
super_secret_command = "aha"
# Youtube Key
youtube_key = ""

# File Info
bot_path = "/path/to/the/bot"
actions_file = bot_path + "liste.json"
stopwords_file = bot_path + "stopwords-fr.txt"

rehost = {
    'folder': '/path/where/to/rehost/images',
    'url': 'url to link',
    'domains': ["usercontent\.irccloud-cdn\.com/", "i\.imgur\.com/", "i\.redd\.it/"]
}
