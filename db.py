#!/usr/bin/env python
# coding: utf-8

from datetime import datetime
from peewee import *
import config as cfg

_db_ = MySQLDatabase(cfg.database['name'],
                     user=cfg.database['user'],
                     passwd=cfg.database['pass'],
                     host=cfg.database['host'])


def close():
    """ Ferme la DB """
    _db_.close()


def create_tables():
    """ Créer les tables """
    if Commandes.table_exists() is False:
        MySQLDatabase.create_tables(_db_, [Commandes, User, Archives, Settings])
        close()


class BaseModel(Model):
    """ Modèle de base """
    class Meta:
        database = _db_


class Commandes(BaseModel):
    """ Classe Commandes """
    id = PrimaryKeyField()
    command = CharField(max_length=120)
    count = IntegerField()


class User(BaseModel):
    """ Classe Pseudo """
    id = PrimaryKeyField()
    last_nickname = CharField(max_length=120)
    registered = BooleanField()
    username = CharField(unique=True, max_length=120)
    normalized_nickname = CharField(max_length=120)
    count_messages = FloatField()
    count_commands = FloatField()
    time_friend = FloatField()
    blacklist = BooleanField()


class Archives(BaseModel):
    """ Classe Archives """
    id = PrimaryKeyField()
    pseudo = ForeignKeyField(User, related_name='pseudo_id')
    timestamp = DateTimeField(default=datetime.now)
    command = ForeignKeyField(Commandes, related_name='commande_id')
    texte = TextField()


class Settings(BaseModel):
    """ Classe Paramètres """
    id = PrimaryKeyField()
    channel = CharField(unique=True)                            # chan actuel
    bot_available = BooleanField(default=True)               # disponibilité du bot
    friend_available = BooleanField(default=True)            # disponibilité de !friend
    friend_available_override = BooleanField(default=True)   # override admin de !friend
    spam_limit = IntegerField(default=5)                     # limite en secondes entre chaque message
    current_friend = ForeignKeyField(User, related_name='actuel', null=True, default=None)      # ami actuel
    prev_friend = ForeignKeyField(User, related_name='precedent', null=True, default=None)      # ami précédent
