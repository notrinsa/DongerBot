#!/usr/bin/env python
# coding: utf-8

__author__ = "rinsa"
__version__ = "1.0"
__date__ = "12/07/2016"
__copyright__ = "Copyright (c) rinsa"
__license__ = "GPL2"

import cgi
from datetime import datetime
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_h
import json
import peewee
from peewee import *
import random
import re
import string
import sys
import time
import urllib2

reload(sys)
sys.setdefaultencoding('utf8')

# Server, Port, ServerPass, Channel, Nick, NickPass
# IRC Server Configuration
SERVER_ADDRESS = "irc.redditairfrance.fr"
PORT = 6697
SERVER_PASSWORD = None
CHANNEL = "#reddit-fr"
# CHANNEL = "#donger"
NICKNAME = "donger"
PASSWORD = "frenchguyez"
ALLOWED_HOSTNAMES = ["mclose.eu"]
# MySQL
DATABASE = MySQLDatabase('db_name', user='', passwd='')
# SUPER_SECRET_COMMAND
SUPER_SECRET_COMMAND = ""

# File Info
PATH = "/opt/bots/donger/"
ACTIONS_FILE = PATH + "liste.json"

STOPWORDS_FILE = 'stopwords-fr.txt'

# Constantes
ARGS_NONE = 0
ARGS_PSEUDO = 1
ARGS_TEXTE = 2
ARGS_SPECIAL = 3
INTERVALS = (
    ('semaines', 604800),  # 60 * 60 * 24 * 7
    ('jours', 86400),    # 60 * 60 * 24
    ('heures', 3600),    # 60 * 60
    ('minutes', 60),
    ('secondes', 1)
)


class BaseModel(Model):
    """ Modèle de base """
    class Meta:
        database = DATABASE


class Stats(BaseModel):
    """ Classe Stats """
    id = peewee.PrimaryKeyField()
    commande = peewee.CharField()
    nombre = peewee.IntegerField()


class Commandes(BaseModel):
    """ Classe Pseudo """
    id = peewee.PrimaryKeyField()
    commande = peewee.CharField()


class Pseudo(BaseModel):
    """ Classe Pseudo """
    id = peewee.PrimaryKeyField()
    pseudo = peewee.CharField()
    normalized_nickname = peewee.CharField()
    temps_ami = peewee.FloatField()
    nombre_messages = peewee.FloatField()
    nombre_commandes = peewee.FloatField()
    blacklist = peewee.BooleanField()


class Archives(BaseModel):
    """ Classe Archives """
    id = peewee.PrimaryKeyField()
    pseudo = peewee.ForeignKeyField(Pseudo, related_name='pseudo_id')
    timestamp = peewee.DateTimeField(default=datetime.now)
    commande = peewee.ForeignKeyField(Commandes, related_name='commande_id')
    texte = peewee.TextField()


class Parametres(BaseModel):
    """ Classe Paramètres """
    bot_available = peewee.BooleanField()               # disponibilité du bot
    friend_available = peewee.BooleanField()            # disponibilité de !friend
    friend_available_override = peewee.BooleanField()   # override admin de !friend
    spam_limit = peewee.IntegerField()                  # limite en secondes entre chaque message
    current_friend = peewee.ForeignKeyField(Pseudo, related_name='actuel')      # ami actuel
    prev_friend = peewee.ForeignKeyField(Pseudo, related_name='precedent')      # ami précédent
    channel = peewee.CharField(primary_key=True)                        # chan actuel


class DongerBot(SingleServerIRCBot):
    def __init__(self, server, port, server_pass=None,
                 nick="timber", nick_pass=None, ssl=True):
        SingleServerIRCBot.__init__(self,
                                    [(server, port, server_pass)],
                                    nick,
                                    nick, True)

        self.chans = CHANNEL
        self.nick_pass = nick_pass

        self.users = []
        self.current_channel = CHANNEL

        self.stopwords = self.load_stopwords()

        self.last_uses = {}
        self.current_friend_time = time.time()

        self.settings = Parametres.get(channel=self.chans)

        self.auteur = None

        self.liste_actions = {}

        print "DongerBot %s" % __version__
        print "Connecting to %s:%i..." % (server, port)
        print "Press Ctrl-C to quit"

    def change_parametre(self, parametre, argument):
        """ Change les paramètres """

        if parametre in ['spamlimit', 'spam_limit', 'spam']:

            # Limite Spam
            if isinstance(int(argument), (int, long)):
                self.save_parametre("spam_limit", argument)

        elif parametre in ['dredi']:
            # Limite Spam
            self.save_parametre("spam_limit", "0")

        elif parametre in ['friends', 'friends_available', 'friend_available', 'friend', 'friend_override']:

            # Amis
            if argument in ['true', '1', 'True']:
                self.save_parametre("friend_available_override", True)
            elif argument in ['false', '0', 'False']:
                self.save_parametre("friend_available_override", False)
                self.save_parametre("current_friend", None)
            elif argument == 'reset':
                self.reset_friends()

        elif parametre in ['donger', 'bot']:

            # Interrupteur
            if argument == 'off':
                self.save_parametre("bot_available", False)
            elif argument == 'on':
                self.save_parametre("bot_available", True)

    def check_time(self):
        """ Regarde l'heure et démarre le !friend ou non """

        if self.settings.friend_available_override is False:
            return
        if 9 > int(time.strftime("%H")) >= 0 and self.settings.friend_available is True:
            self.save_parametre("friend_available", False)
        elif int(time.strftime("%H")) >= 9 and self.settings.friend_available is False:
            self.save_parametre("friend_available", True)
            self.save_parametre("prev_friend", None)
            self.save_parametre("current_friend", None)

    def ecrit_random(self, reste):
        """ Gère le random yo """

        commande = self.liste_actions[random.choice(self.liste_actions.keys())]
        """ Random commande """

        reste = random.choice(self.users) \
            if reste is None and commande['args'] == ARGS_PSEUDO \
            else reste
        """ Si la commande sortie nécessite un user et qu'il n'y a pas de reste, on prend un utilisateur au pif"""

        if commande['args'] == ARGS_SPECIAL:
            return

        if reste is not None:
            """ Cas où reste = texte et s'il y a un argument ou si la commande demande un pseudo et l'arg en est un """
            retour = self.ecrit_donger(commande, reste) \
                if (commande['args'] == ARGS_PSEUDO and reste in self.users) or commande['args'] == ARGS_TEXTE \
                else self.ecrit_random(reste)
            """Si la commande sortie n'accepte pas d'argument texte, on re-random"""
            return retour

        else:
            """ Si on tombe ici c'est que la commande ne veut pas d'argument, donc on écrit le donger """
            retour = self.ecrit_donger(commande) \
                if commande['args'] == ARGS_NONE \
                else self.ecrit_random(reste)
            return retour

    def ecrit_donger(self, donger, reste=None):
        """ Formate le donger """
        reste = donger['default'] if reste is None and donger['default'] is not None else reste
        reste = reste.upper() if donger['caps'] is True and reste is not None else reste

        donger_action = donger['action']
        donger_commande = donger['commande']

        message = None

        if donger['args'] == ARGS_SPECIAL:
            """ Commandes spéciales """

            if donger_commande == "!photo":
                """ Commande photo """
                message = donger_action.format(reste) + "" + self.id_generator()

            if donger_commande == "!afol":
                """ Commande AFOL """
                reste = reste.decode("utf-8", "ignore")
                collection = reste + 's' if reste[-1:] != 's' else reste
                initiales = ""
                for i in reste.upper().split():
                    initiales += i[0]
                message = donger_action.format(*[initiales, reste.title(), collection])

            if donger_commande == "!anniv":
                """ Commande anniv """
                if reste is None:
                    return None
                mots = reste.split(" ")
                if len(mots) < 2:
                    return None
                message = donger_action.format(*[mots[0], mots[1]]) \
                    if mots[1].isdigit() and len(mots[1]) < 4 and len(mots[0]) < 30 \
                    else None

            if donger_commande == "!who":
                """ Commande who """
                try:
                    reste = self.settings.current_friend.pseudo
                except Pseudo.DoesNotExist:
                    reste = "Personne"
                message = donger_action.format(reste)

            if donger_commande == "!friend":

                try:
                    prev_friend = self.settings.prev_friend
                except Pseudo.DoesNotExist:
                    prev_friend = None

                try:
                    current_friend = self.settings.current_friend
                except Pseudo.DoesNotExist:
                    current_friend = None

                """ Commande friend """
                if self.settings.friend_available_override is False:  # Override admin !friend
                    return
                if self.settings.friend_available is False:  # dispo !friend naturel
                    return
                if (prev_friend is not None
                    and self.auteur['n'].lower() == self.settings.prev_friend.normalized_nickname) \
                        or (current_friend is not None
                            and self.auteur['n'].lower() == self.settings.current_friend.normalized_nickname):
                    """ Si l'auteur est l'ami en cours ou l'ami précédent """
                    return

                if current_friend is None:
                    message = "⭐️ {0} ⭐️ est mon 🥇 premier 🥇 ❤️ meilleur ami ❤️ de la 🌞 journée 🌞" \
                        .format(self.auteur['n'])

                elif current_friend is not None \
                        and self.settings.current_friend.normalized_nickname != self.auteur['n'].lower():
                    message = donger_action.format(self.settings.current_friend.pseudo, self.auteur['n'])
                    self.save_parametre('prev_friend', current_friend)

                """ ORM Ami """
                try:
                    auteur = Pseudo.get(Pseudo.normalized_nickname == self.auteur['n'].lower())
                except Pseudo.DoesNotExist:
                    auteur = Pseudo.create(pseudo=self.auteur['n'], normalized_nickname=self.auteur['n'].lower())
                self.save_parametre('current_friend', auteur)  # Changement de l'ami de donger
                self.refresh_friends()

        else:
            """ Si la commande nécessite un pseudo et qu'il n'y en a pas, on random un utilisateur """
            if reste is None and (donger['args'] == ARGS_PSEUDO or donger['args'] == ARGS_TEXTE):
                reste = random.choice(self.users)

            if reste is not None:
                if donger['args'] == ARGS_PSEUDO and reste.lower() not in self.users and reste != donger['default']:
                    pass
                else:
                    message = donger_action.format(reste)
            else:
                message = donger_action

        return message

    def get_friends(self, friend=None):
        """ Récupération des stats des amis """

        if friend is not None:

            """ ORM Récup friend """
            try:
                ami = Pseudo.get(Pseudo.normalized_nickname == friend.lower())
                sendmsg = friend + " a été le meilleur ami de donger pendant " + str(self.display_time(ami.temps_ami))
            except Pseudo.DoesNotExist:
                sendmsg = friend + " n'a jamais été le meilleur ami de donger :("

        else:

            """ ORM Récup top friends """
            sendmsg = "Les 5 meilleurs amis de donger : "
            for ami in Pseudo.select().order_by(Pseudo.temps_ami.desc()).limit(5):
                sendmsg += ami.pseudo + " pendant " + self.display_time(ami.temps_ami) + "; "
            sendmsg = sendmsg[:-2]

        return sendmsg

    def get_stats(self, commande):
        """ Récupère les stats d'une commande """

        if commande is not None:

            """ ORM Récup stats commande """
            _commande, created = Stats.get_or_create(commande=commande)
            sendmsg = "Stats pour la commande " + commande + " : envoyée " + str(_commande.nombre) + " fois" \
                if created is False \
                else "Pas de stats pour la commande " + commande + "."

        else:

            """ ORM Récup top stats """
            sendmsg = "5 commandes les plus utilisées :  "
            for commandes in Stats.select().order_by(Stats.nombre.desc()).limit(5):
                sendmsg += commandes.commande + " : " + str(commandes.nombre) + " fois    "

        self.ferme_connexion()

        return sendmsg

    def ignore_user(self, user, remove):
        """ Ignore un utilisateur """
        try:
            pseudo = Pseudo.get(Pseudo.normalized_nickname == user.lower())
        except Pseudo.DoesNotExist:
            pseudo = Pseudo.create(pseudo=user, normalized_nickname=user.lower())

        pseudo.blacklist = remove
        pseudo.save()
        self.ferme_connexion()

    def on_privmsg(self, c, infos):
        message = infos.arguments()[0].rstrip()
        # Traite Event
        self.traite_event(infos)
        # Traite Message
        self.traite_message(c, message, infos)

        """ Log """
        self.write_log("privmsg", infos)

    def on_pubmsg(self, c, infos):
        """ Traitement des messages publics """

        message = infos.arguments()[0].rstrip()

        """ Traite Event """
        self.traite_event(infos)

        """ Traite le message """
        self.traite_message(c, message, infos)

    def on_welcome(self, c, e):
        """Join channels after successful connection"""
        if self.nick_pass:
            c.privmsg("nickserv", "identify %s" % self.nick_pass)
            c.join(self.chans)

    def quit(self):
        self.connection.disconnect("ヽ༼ຈل͜ຈ༽ﾉ ")

    def refresh_friends(self):
        """ Rafraichit le temps de l'ami actuel """

        if self.settings.friend_available_override is False:
            return

        if self.settings.friend_available is True:
            """ ORM Get User"""
            try:
                ami = Pseudo.get(Pseudo.id == self.settings.current_friend)
                ami.temps_ami += round(time.time() - self.current_friend_time)
                ami.save()
                self.ferme_connexion()
                self.current_friend_time = time.time()

            except Pseudo.DoesNotExist:
                pass

    def reset_friends(self):
        """ Reset les amis """

        query = Pseudo.update(temps_ami=0)
        query.execute()

        self.ferme_connexion()

    def save_parametre(self, parametre, argument):
        setattr(self.settings, parametre, argument)
        self.settings.save()
        self.ferme_connexion()

    def send_pub_msg(self, connection, message):
        [connection.privmsg(self.chans, msg) for msg in message.splitlines()]

    def traite_message(self, connection, message, infos):
        """ Traite les messages (nombre messages) """

        """ ORM Maj Utilisateur """
        try:
            user = Pseudo.get(Pseudo.normalized_nickname == self.auteur['n'].lower())
        except Pseudo.DoesNotExist:
            user = Pseudo.create(pseudo=self.auteur['n'], normalized_nickname=self.auteur['n'].lower())
        user.nombre_messages = user.nombre_messages + 1 if user.nombre_messages is not None else 1
        user.save()
        self.ferme_connexion()

        # Partie Commande / Action
        if message.startswith("!") and len(message) > 2:
            # Jarte le "!"
            message = message[1:]
            # Récupère l'intitulé de la commande
            commande = re.split('(\W)+', message, 1)[0]
            # Dégage la commande du reste du message
            reste = message[len(commande) + 1:] if len(message[len(commande) + 1:]) > 0 else None

            """
                Vérifications floods / disponibilités du bot hors admin
                > Si le bot est disponible
                > Si l'utilisateur n'est pas dans ceux blacklistés
                > Si l'utilisateur n'a pas lancé de code avant la spam_limit
            """

            if self.auteur['m'] not in ALLOWED_HOSTNAMES:
                # Bot désactivé
                if self.settings.bot_available is False:
                    return
                # Utilisateurs blacklistés
                try:
                    Pseudo.get(Pseudo.normalized_nickname == self.auteur['n'].lower(), Pseudo.blacklist is True)
                    return
                except Pseudo.DoesNotExist:
                    pass
                if self.auteur['fn'] not in self.last_uses:
                    # Rajout dans le filtre
                    self.last_uses[self.auteur['fn']] = time.time()
                else:
                    if int(round(time.time() - self.last_uses[self.auteur['fn']])) < int(self.settings.spam_limit):
                        return
                    else:
                        self.last_uses[self.auteur['fn']] = time.time()

            # Chargement de la liste des actions
            self.liste_actions = self.load_file()

            envoi_message = None

            """
                dispatch principal
            """
            if commande.lower() in self.liste_actions:
                envoi_message = self.ecrit_donger(self.liste_actions[commande.lower()], reste)

            """
                dispatch spécial, admin
            """
            if self.auteur['m'] in ALLOWED_HOSTNAMES:
                if commande.lower() in ["blacklist", "degage"]:
                    # Partie blacklist / ignore_user(pseudo, true)
                    self.ignore_user(reste, True)
                if commande.lower() in ["unignore", "remove", "un"]:
                    # Partie unignore / ignore_user(pseudo, false)
                    self.ignore_user(reste, False)
                if commande.lower() in ["setting", "set", "param", "parameter"]:
                    # Partie Settings / set_param(param, arg)
                    _message = re.split("(\W+)", reste)
                    if len(_message) != 3:
                        return
                    parametre = _message[0]
                    argument = _message[2]
                    self.change_parametre(parametre, argument)
                if commande.lower() in ["get"]:
                    try:
                        if getattr(self.settings, reste, None) is not None:
                            envoi_message = "Paramètre " + reste + " : " + str(getattr(self.settings, reste))
                    except Pseudo.DoesNotExist:
                        envoi_message = "Pas de pseudo sélectionné"

            """
                dispatch spécial, not admin
            """
            if commande.lower() == "liste":
                # Partie Liste / send_msg
                envoi_message = "La liste des commandes est disponible sur www.redditairfrance.fr"

            if commande.lower() == "random":
                # Partie Random / get_random
                envoi_message = self.ecrit_random(reste)

            if commande.lower() == "stats":
                # Partie Stats / get_stats
                envoi_message = self.get_stats(reste)

            if commande.lower() == "friends":
                # Partie Friends / get_friends
                envoi_message = self.get_friends(reste)

            if commande.lower() == SUPER_SECRET_COMMAND:
                # Partie commande secrete
                envoi_message = reste

            if envoi_message is not None:
                self.send_pub_msg(connection, envoi_message if commande.islower() else envoi_message.upper())
                self.traite_donger(commande.lower(), reste)

        elif message.startswith(".") and len(message) > 2:
            # Jarte le "!"
            message = message[1:]
            # Récupère l'intitulé de la commande
            commande = re.split('(\W)+', message, 1)[0]
            # Dégage la commande du reste du message
            reste = message[len(commande) + 1:] if len(message[len(commande) + 1:]) > 0 else None

            envoi_message = self.traite_service(commande, reste)
            self.send_pub_msg(connection, envoi_message)

        else:
            """ Log message """
            self.write_log("pubmsg", infos)

    def traite_donger(self, commande, reste=None):
        """ Envoi le donger sur le chan et traitements annexes (logs, sql, friends, check_time ...) """

        """ ORM Ajout stats commandes """
        stats, created = Stats.get_or_create(commande=commande, defaults={'nombre': 1})
        if created is False:
            stats.nombre += 1
            stats.save()

        """ ORM Ajout archives """
        try:
            user = Pseudo.get(Pseudo.normalized_nickname == self.auteur['n'].lower())
        except Pseudo.DoesNotExist:
            user = Pseudo.create(pseudo=self.auteur['n'], normalized_nickname=self.auteur['n'].lower())

        Archives.create(pseudo_id=user, commande=stats, texte=reste)
        user.nombre_commandes = user.nombre_commandes + 1 if user.nombre_commandes is not None else 1
        user.save()

        self.ferme_connexion()

    def traite_event(self, infos):
        # refresh actual friend
        self.refresh_friends()

        # Récupère l'auteur
        self.auteur = {
            'fn': infos.source(),  # fullname  (rinsa!rinsa@mclose.eu)
            'f': self.nm_to_fn(infos.source()),  # full      (rinsa@mclose.eu)
            'm': nm_to_h(infos.source()),  # mask      (mclose.eu)
            'n': nm_to_n(infos.source())  # nickname  (rinsa)
        }

        self.check_time()
        self.current_channel = self.channels[CHANNEL]
        self.users = [pseudo.lower() for pseudo in self.current_channel.users()]

    @staticmethod
    def display_time(seconds, granularity=5):
        """ affiche le temps correctement par rapport à un nombre de secondes """

        result = []
        for name, count in INTERVALS:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(str(value)[:-2], name))
        return ', '.join(result[:granularity])

    @staticmethod
    def ferme_connexion():
        DATABASE.close()

    @staticmethod
    def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    @staticmethod
    def load_file():
        """ Récupère le fichier des actions """
        with open(ACTIONS_FILE) as data_file:
            actions = json.load(data_file)
        full_list = {}
        # On aplatit le fichier JSON en enlevant les catégories
        for key in actions:

            for dkey in actions[key]:
                donger = {
                    'action': actions[key][dkey]['action'],
                    'commande': actions[key][dkey]['commande'],
                    'args': actions[key][dkey]['args'] if 'args' in actions[key][dkey] else 0,
                    'caps': actions[key][dkey]['caps'] if 'caps' in actions[key][dkey] else None,
                    'default': actions[key][dkey]['default'] if 'default' in actions[key][dkey] else None
                }

                full_list[actions[key][dkey]['commande'][1:]] = donger

        return full_list

    @staticmethod
    def load_stopwords():
        """ Récupère les mots non importants """
        with open(STOPWORDS_FILE) as data_file:
            return data_file.read().split()

    @staticmethod
    def nm_to_fn(auteur):
        return auteur.split("!")[1]

    @staticmethod
    def traite_service(commande, reste):
        """ Permet la récupération de la balise <title /> pour certaines pages comme YT, Spotify ... """

        message = None

        # Spotify
        if commande == "spotify" and reste is not None:
            track_id = re.sub(r'^spotify:|https://[a-z]+\.spotify\.com/track/', '', reste)
            try:
                req = urllib2.Request('https://open.spotify.com/track/' + track_id)
                req.add_header('Range', 'bytes={}-{}'.format(0, 99))
                f = urllib2.urlopen(req)
                soup = BeautifulSoup(f.read(), 'html.parser')
                message = "Track Spotify: {0} https://open.spotify.com/track/{1}".format(soup.title.string, track_id)
            except urllib2.URLError as e:
                message = e.message.decode("utf8", 'ignore')

        return message

    @staticmethod
    def on_nicknameinuse(c, e):
        c.nick(c.get_nickname() + "_")

    def write_log(self, action, event):
        timestamp = time.time()*1000
        sender = nm_to_n(event.source())
        channel = event.target()
        content = cgi.escape(event.arguments()[0]) if len(event.arguments()) > 0 else None

        info_content = None
        if action is 'pubmsg':
            phrase = content.lower()
            words = phrase.split()
            important_words = []

            for word in words:
                word = word.strip(string.punctuation)
                if word not in self.stopwords and len(word) > 0:
                    important_words.append(word.decode('utf-8', 'ignore'))

            info_content = {
                'content': content,
                'raw': important_words
            }

        message = {
            'date': timestamp,
            'action': action,
            'nickname': {
                "original": sender,
                "normalized": sender.lower()
            },
            'channel': channel,
            'info_message': info_content
        }

        es = Elasticsearch()
        es.index(index="messages", doc_type="message", body=message)
        es.indices.refresh(index="messages")

    def on_action(self, c, e):
        self.write_log("action", e)

    def on_join(self, c, e):
        self.write_log("join", e)

    def on_kick(self, c, e):
        self.write_log("kick", e)

    def on_mode(self, c, e):
        self.write_log("mode", e)

    def on_part(self, c, e):
        self.write_log("part", e)

    def on_pubnotice(self, c, e):
        self.write_log("pubnotice", e)

    def on_quit(self, c, e):
        self.write_log("quit", e)


def main():
    # Start the bot
    bot = DongerBot(SERVER_ADDRESS, PORT, SERVER_PASSWORD, NICKNAME, PASSWORD)
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.quit()


if __name__ == "__main__":
    main()
