#!/usr/bin/env python
# coding: utf-8

__author__ = "rinsa"
__version__ = "0.1"
__date__ = "12/07/2016"
__copyright__ = "Copyright (c) rinsa"
__license__ = "GPL2"


import cgi
import os
import ftplib
import sys
import itertools
import time
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
from irclib import nm_to_n

import re
import shlex
import json
import codecs
import random

from pprint import pprint

# IRC Server Configuration
SERVER = ""
PORT = 6667
SERVER_PASS = None
__channel__ = ""
__nick__ = "dongerz"
__nickpass__ = ""
__logpath__ = "/path/to/the/log/folder"
__super_secret_command__ = "!repeat"

DEFAULT_TIMEZONE = 'GMT+2'

### DongerBot class
class DongerBot(SingleServerIRCBot):
    def __init__(self, server, port, server_pass=None, channels=[],
                 nick="timber", nick_pass=None):
        SingleServerIRCBot.__init__(self,
                                    [(server, port, server_pass)],
                                    nick,
                                    nick)

        self.chans = __channel__
        self.superspam = 0
        self.lastmessage = 0
        self.nick_pass = nick_pass

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

    def on_nicknameinuse(self, c, e):
        """Nickname in use"""
        c.nick(c.get_nickname() + "_")

    def on_privmsg(self, connection, infos):
        chan = self.channels[__channel__]
        users = chan.users()
        message = infos.arguments()[0].rstrip()
        if re.search("^!\w+", message):
            commande = re.findall("^!\w+", message)
            if commande[0] == __super_secret_command__:
                self.send_pub_msg(connection, message.replace(__super_secret_command__ + " ", ""))
                message = "[" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + "]   " + nm_to_n(infos.source()) + " : " + message.replace("!repeat ", "") + "\n"
                self.write_log_file(message, __logpath__ + "log_repeat_" + strftime("%Y-%m-%d", localtime()) + ".txt")
                return
        self.send_donger(connection, infos, __channel__, users)

    def send_pub_msg(self, connection, message):
        connection.privmsg(__channel__, message)

    def write_log_file(self, message, file):
        fo = open(file, "a")
        fo.write(message)
        fo.close
    
    def on_pubmsg(self, connection, infos):
        auteur = nm_to_n(infos.source())
        canal = (infos.target(), self.channels[infos.target()])
        users = canal[1].users()
        chan = canal[0]
        self.send_donger(connection, infos, chan, users)
        
    def format_message(self, actions, commande, message, users):
        # on split les arguments
        args = re.split('\s', message)
        # on supprime le nom de la commande
        del args[0]
        # on recup' le nombre d'arguments
        taille = len(args)
        newstr = actions[commande[0]]
        nbmin = len(re.split("\$\w+", newstr)) - 1
        # if (nbmin == taille and time.time() - self.lastmessage > 1.5): # pour eviter le spam
        if nbmin == taille:
            # on remplace les $x par les arguments
            for i in range(0, taille):
                # on verifie si le pseudo existe bien pour eviter n'imp
                if args[i] not in users:
                    return False
                # commandes qui changent le pseudo en majuscule
                if commande[0] in ["!aura"]:
                    args[i] = args[i].upper()
                newstr = newstr.replace("$" + str(i + 1), args[i])
            # on envoie le message
            return newstr
        else:
            return False
    
    def create_list(self, actions):
            # declaration du tableau pour toute les commandes
            listearray = []
            listearray.append("Commandes disponibles : ")
            # on parcourt les cles du dictionnaire d'actions
            for key, value in actions.iteritems():
                # affichage de la commande mise en forme
                listestr = ""
                listestr += key
                diffargs = re.findall("\$\w+", value)
                # si la commande possede des arguments, on rajoute pseudo + numero de l'argument e la suite
                for i in range(0, len(diffargs)):
                    listestr += " {pseudo " + str(i + 1) + "}"
                listestr += ", "
                listearray.append(listestr)
            list2send = []
            jump = 0
            maximum = 10 # nombre maximum de commandes par ligne
            for k in range(0, len(listearray)):
                if jump == k:
                    max = len(listearray) - k
                    superstr = ""
                    if max < maximum:
                        for l in range (k, len(listearray)):
                            # list2send.append(listearray[l].encode('utf-8', 'ignore'))
                            superstr += listearray[l].encode('utf-8', 'ignore')
                        list2send.append(superstr[:-2])
                    else:
                        for l in range (k, k + maximum):
                            # list2send.append(listearray[l].encode('utf-8', 'ignore'))
                            superstr += listearray[l].encode('utf-8', 'ignore')
                        list2send.append(superstr)
                    jump = k + maximum
            self.lastmessage = time.time()
            return list2send
            
            
    def send_donger(self, connection, infos, target, users):
        
        auteur = nm_to_n(infos.source())
        canal = (target, connection)
        message = infos.arguments()[0].rstrip()
        
        # trigger d'insultes si on prononce le pseudo du bot
        if __nick__ in message:
            with open('/home/rinsa/pastabot/insultes.json') as insultes_file:    
                insultes = json.load(insultes_file)
            # insulte R A N D O M
            insulte = random.choice(insultes.items())
            # si l'insulte a un argument, on le remplace
            insulte = insulte[1].replace("$1", auteur)
            # timer 1 seconde pour simuler un comportement humain
            time.sleep(1)
            connection.privmsg(canal[0], insulte.encode('utf-8', 'ignore'))
            return
            
        # on ouvre le fichier d'actions
        with open('/home/rinsa/pastabot/actions.json') as data_file:    
            actions = json.load(data_file)
            
        # si le message envoye sur le chan commence par ! / on fait pas de verification si la commande existe car il y a des commandes prises en compte et non listee
        if re.search("^!\w+", message):
            # on recupere le nom de la commande
            commande = re.findall("^!\w+", message)
            
            # la liste !
            if commande[0] == "!liste":
                # on evite le spam, envoi possible toutes les 5 minutes ///// 20 secondes maintenant car envoi de la liste via mp
                if time.time() - self.lastmessage < 20:
                    if time.time() - self.superspam < 9:
                        self.superspam = time.time()
                        return
                    elif time.time() - self.superspam > 1.5:
                        connection.privmsg(auteur, "ça va le spam ou quoi ?")
                        self.superspam = time.time()
                        return
                    else:
                        return
                # on créé le tableau des commandes dispos
                liste = self.create_list(actions)
                for li in range(0, len(liste)):
                    connection.privmsg(auteur, liste[li])
                    # on envoie la commandes toutes les secondes et demi pour éviter un mass flood
                    time.sleep(1.5)
                    
            # donc on verifie si la commande existe bien dans la liste des actions
            if commande[0] in actions:
                sendmsg = self.format_message(actions, commande, message, users)
                if sendmsg is not False:
                    # on envoie le message dans le canal spécifié
                    connection.privmsg(canal[0], sendmsg.encode('utf-8', 'ignore'))
                    # on créé le message de log au format [DATE] pseudo : commande 
                    log_message = "[" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + "]   " + nm_to_n(auteur) + " : " + message + "\n"
                    # on écrit le message dans le fichier de log
                    self.write_log_file(log_message, __logpath__ + "log_public_" + strftime("%Y-%m-%d", localtime()) + ".txt")
                    

def main():
    # Start the bot
    bot = DongerBot(SERVER, PORT, SERVER_PASS, __channel__, __nick__, __nickpass__)
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.quit()

if __name__ == "__main__":
    main()
