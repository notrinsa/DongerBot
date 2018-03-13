#!/usr/bin/env python
# coding: utf-8

from datetime import datetime
import peewee
from peewee import *
import config as cfg
import locale

locale.setlocale(locale.LC_ALL, 'fr_FR')

_db_ = MySQLDatabase(cfg.database['name'], user=cfg.database['user'], passwd=cfg.database['pass'])


def close():
    """ Ferme la DB """
    _db_.close()


class BaseModel(Model):
    """ Modèle de base """
    class Meta:
        database = _db_


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

    def __init__(self, nick, host, name):
        super(BaseModel, self).__init__()


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
