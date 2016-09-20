#!/usr/bin/env python
# coding: utf-8

__author__ = "rinsa"
__version__ = "1.1"
__date__ = "2016-09-20"
__copyright__ = "Copyright (c) rinsa"
__license__ = "GPL2"


import cgi
import os
from os import path
from collections import OrderedDict
import ftplib
import sys
reload(sys)  
sys.setdefaultencoding('utf8')
import itertools
import time
import random
from time import strftime, localtime
try:
    from datetime import datetime
    from pytz import timezone
except: pass

try:
    from hashlib import md5
except:
    import md5

from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h

import re
import shlex
import json
import codecs
import random

from pprint import pprint

# IRC Server Configuration
SERVER = "0.0.0.0"
PORT = 6667
SERVER_PASS = None
CHANNEL = "#!"
NICK = "donger"
NICKPASS = ""
DEFAULT_TIMEZONE = 'GMT+2'
# File Info
LOCATION_PATH = "/path/to/where/the/bot/is/located"
LOGPATH = LOCATION_PATH + "logs/"
BLACKLIST = LOCATION_PATH + "blacklist.txt"
ACTIONS_FILE = LOCATION_PATH + "liste.json"
STATS_FILE = LOCATION_PATH + "stats.json"
#
SS_COMMAND = "!repeat"
HOSTNAME_OP = "maisonclo.se" # a static mask is preferred
# MY OLD FRIEND
CURRENT_FRIEND = "donger"

### DongerBot class

class DongerBot(SingleServerIRCBot):
    def __init__(self, server, port, server_pass=None, channels=[],
                 nick="donger", nick_pass=None):
        SingleServerIRCBot.__init__(self,
                                    [(server, port, server_pass)],
                                    nick,
                                    nick)

        self.chans = CHANNEL
        self.nick_pass = NICKPASS

        print "DongerBot %s" % __version__
        print "Connecting to %s:%i..." % (server, port)
        print "Press Ctrl-C to quit"

    def quit(self):
        self.connection.disconnect("ヽ༼ຈل͜ຈ༽ﾉ ")

    def on_welcome(self, c, e):
        """Join channels after successful connection"""
        if self.nick_pass:
            c.privmsg("nickserv", "identify %s" % self.nick_pass)
            c.join(self.chans)

    # si le nom d'utilisateur est déjà utilisé, rajout d'underscore
    def on_nicknameinuse(self, c, e):
        """Nickname in use"""
        c.nick(c.get_nickname() + "_")
    
    # Traitement des messages privés
    def on_privmsg(self, connection, infos):
        chan = self.channels[CHANNEL]
        users = chan.users()
        message = infos.arguments()[0].rstrip()
        if re.search("^!\w+", message):
            commande = re.findall("^!\w+", message)
            if commande[0] == SS_COMMAND:
                self.send_pub_msg(connection, message.replace(SS_COMMAND + " ", ""))
                message = "[" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + "]   " + nm_to_n(infos.source()) + " : " + message.replace("!repeat ", "") + "\n"
                self.write_file(message, LOGPATH + "log_repeat_" + strftime("%Y-%m-%d", localtime()) + ".txt")
                return
        self.send_donger(connection, infos, CHANNEL, users)
    
    # Traitement des messages publics
    def on_pubmsg(self, connection, infos):
        canal = (infos.target(), self.channels[infos.target()])
        users = canal[1].users()
        chan = canal[0]
        message = infos.arguments()[0].rstrip()
        if message.startswith("!") and len(message) > 1:
            self.send_donger(connection, infos, chan, users)
    
    # envoie un message dans le channel
    def send_pub_msg(self, connection, message):
        connection.privmsg(CHANNEL, message)

    # fonction d'écriture de fichier
    def write_file(self, message, file):
        fo = open(file, "a")
        fo.write(message)
        fo.close

    # rajoute un utilisateur / mask dans le fichier de blacklist
    def ignore_user(self, user, mask=""):
        ignored = self.get_ignored_users()
        # if (user not in ignored and mask not in ignored):
            # self.write_file(user + "\n" + mask + "\n", __blacklist_file__)
        if (user not in ignored):
            self.write_file(user + "\n", BLACKLIST)

    # retire une ligne du fichier blacklist
    def unignore(self, user, mask=""):
        f = open(BLACKLIST, "r")
        lines = f.readlines()
        f.close()
        f = open(BLACKLIST, "w")
        for line in lines:
            # if (line != user + "\n" or line != mask + "\n"):
            if (line != user + "\n"):
                f.write(line)
        f.close
        
    # écris dans le fichier de stats
    def w_stats_donger(self, donger):
        lines = self.load_stats()
        if donger not in lines:
            lines[donger] = 1
        else:
            lines[donger] += 1
        f = open(STATS_FILE, "w")
        f.write(json.dumps(lines))
        
    # récupère les stats
    def get_stats(self, message):
        stats = OrderedDict(sorted(self.load_stats().items(), key=lambda t: t[1]))
        stats = OrderedDict(reversed(list(stats.items())))
        
        args = re.split('\s', message)
        full_message = message
        # on supprime le nom de la commande
        if len(args) > 1:
            commande = message.replace(args[0], "", 1)
            commande = commande.strip()
        else:
            commande = None
        
        if (len(stats) < 5):
            length_stats = len(stats)
        else:
            length_stats = 5
        
        if (commande is not None):
            if (commande in stats):
                sendmsg = "×× Stats pour la commande " + commande + " : envoyée " + str(stats[commande]) + " fois ××"
            else:
                sendmsg = "×× Pas de stats pour la commande " + commande + " ! Peut-être serait-il temps d'en lancer une ? ××"
        else:
            sendmsg = "×× 5 commandes les plus utilisées ×× ×× "
            for key, value in list(stats.items())[:5]:
                sendmsg += key + " : " + str(value) + " fois ×× "
            sendmsg = sendmsg + "××"
        return sendmsg

    # récupère chaque utilisateur blacklisté
    def get_ignored_users(self):
        if os.path.exists(BLACKLIST) is False:
            return []
        with open(BLACKLIST) as fo:
            ignored_users = fo.read().splitlines()
            return ignored_users
    
    # formate le message de sortie
    def format_message(self, donger, message, users, auteur):
        # on split les arguments
        args = re.split('\s', message)
        full_message = message
        # on supprime le nom de la commande
        if len(args) > 1:
            message = message.replace(args[0], "", 1)
            message = message.strip()
        else:
            message = None

        # On balance chacune des infos si elles existent dans des variables
        donger_msg = donger['action']
        if 'args' in donger:
            donger_args = donger['args']
            donger_caps = donger['caps']
            if 'default' in donger:
                donger_default = donger['default']
            else:
                donger_default = None
        else:
            donger_args = 0
            
        # donger_args à 1 = pseudos
        if donger_args == 1:
            if message is not None:
                # si l'argument n'est pas vide et contient un utilisateur, sinon on dégage
                if message.upper() in (user.upper() for user in users):
                    if donger_caps:
                        send_msg = donger_msg % message.upper()
                    else:
                        send_msg = donger_msg % message
                else:
                    send_msg = False
            elif message is None:
                # si l'argument est vide et si le default n'est pas vide, sinon on dégage
                if donger_default is not None:
                    if donger_caps:
                        send_msg = donger_msg % donger_default.upper()
                    else:
                        send_msg = donger_msg % donger_default
                else:
                    send_msg = False
            else:
                return
        # donger_args à 2 = texte
        elif donger_args == 2:
            # si y a pas de texte, on dégage
            if message is not None:
                send_msg = donger_msg % message
            else:
                send_msg = False
        # donger_args à 3 = spécial
        elif donger_args == 3:
            # si la commande est !who, on dit qui est l'ami actuel
            if donger['commande'] == '!who':
                send_msg = donger_msg.format(CURRENT_FRIEND)
            elif donger['commande'] == '!friend':
                # si l'ami actuel est différent de l'auteur, on change celui-ci et donger est content
                if CURRENT_FRIEND != auteur:
                    send_msg = donger_msg.format(CURRENT_FRIEND, auteur.upper())
                    self.change_friend(auteur)
                # sinon on renvoie un !who, mais comme je suis trop nul j'ai écrit en dur
                else:
                    send_msg = "⭐️ {0} ⭐️ est mon ❤️ meilleur ami ❤️".format(CURRENT_FRIEND)
        # donger_args à 0 / None / null
        else:
            send_msg = donger_msg
            
        # return
        message = "[" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + "]   " + auteur + " : " + full_message + "\n"
        self.write_file(message, LOGPATH + "log_command_" + strftime("%Y-%m-%d", localtime()) + ".txt")
        return send_msg
        
    # oui je suis ton ami
    def change_friend(self, new):
        global CURRENT_FRIEND
        CURRENT_FRIEND = new

    # charge le fichier de stats
    def load_stats(self):
        with open(STATS_FILE) as data_file:    
            actions = json.load(data_file)
        return actions
        
    # Récupère le fichier JSON
    def load_file(self):
        with open(ACTIONS_FILE) as data_file:    
            actions = json.load(data_file)   
        full_list = {}
        # On aplatit le fichier JSON en enlevant les catégories
        for key in actions:
            for dkey in actions[key]:
                donger = {}
                donger['action'] = actions[key][dkey]['action'] 
                donger['commande'] = actions[key][dkey]['commande'] 
                if 'args' in actions[key][dkey]:
                    donger['args'] = actions[key][dkey]['args']
                    donger['caps'] = actions[key][dkey]['caps']
                    if 'default' in actions[key][dkey]:
                        donger['default'] = actions[key][dkey]['default']
                full_list[actions[key][dkey]['commande'] ] = donger
        return full_list
    
    # Pas de fonction native à la lib qui permet de récupérer le nom@mask :|
    def nm_to_fn(self, auteur):
        return auteur.split("!")[1]
    
    # On envoie le donger
    def send_donger(self, connection, infos, target, users):
        auteur_full = infos.source()
        auteur_fn = self.nm_to_fn(auteur_full)
        auteur_mask = nm_to_h(auteur_full)
        auteur = nm_to_n(auteur_full)
        canal = (target, connection)
        message = infos.arguments()[0].rstrip()
        if auteur_fn in self.get_ignored_users():
            return

        # on ouvre le fichier d'actions
        liste = self.load_file()

        # on récupère la commande
        pattern = re.compile("^!\w+")
        if pattern.match(message):
            commande = re.findall("^!\w+", message)[0]
        else:
            return
        
        # commande dans la liste ?
        if commande in liste:
            sendmsg = self.format_message(liste[commande], message, users, auteur)
            self.w_stats_donger(commande)
            if sendmsg is False:
                return
            else:
                self.send_pub_msg(connection, sendmsg.encode('utf-8', 'ignore'))
        # Commande !blacklist !unignore
        elif commande in ['!blacklist', '!unignore'] and auteur_mask == 'maisonclo.se':
            args = re.split('\s', message)
            if len(args) == 2:
                message = message.replace(args[0], "", 1)
                message = message.strip()
            else:
                return
            if commande == '!blacklist':
                self.ignore_user(message)    
            if commande == '!unignore':
                self.unignore(message)
        # Commande !liste
        elif commande == '!liste':
            self.send_pub_msg(connection, "La liste des commandes est disponible sur www.redditairfrance.fr")
        # Envoie une commande au hasard avec un utilisateur au hasard
        elif commande == '!random':
            r_commande = liste[random.choice(liste.keys())]
            if 'args' in r_commande and r_commande['args'] == 2:
                return
            r_user = random.choice(users)
            r_message = r_commande['commande'] + " " + r_user
            sendmsg = self.format_message(r_commande, r_message, users, auteur)
            if sendmsg is False:
                return
            self.send_pub_msg(connection, sendmsg.encode('utf-8', 'ignore'))
        elif commande == '!stats':
            sendmsg = self.get_stats(message)
            if sendmsg is False:
                return
            else:
                self.send_pub_msg(connection, sendmsg)
                
def main():
    # Start the bot
    bot = DongerBot(SERVER, PORT, SERVER_PASS, CHANNEL, NICK, NICKPASS)
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.quit()

if __name__ == "__main__":
    main()
