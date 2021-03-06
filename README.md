DongerBot 2
============

Codé par rinsa <me@ben.ovh> pour #reddit-fr / /r/France, avec comme base modifiée LogBot créé par Chris Oliver <chris@excid3.com>

Utilisation
-----

Le bot nécessite Python2 pour fonctionner.  
Pour lancer le bot, il suffit d'exécuter le script comme n'importe quel autre script python

    python dongerbot.py


Commandes disponibles
-----

Les différentes actions sont contenues dans le fichier **liste.json**  
L'argument utilisé et pris en compte est %s. Pour que celui-ci soit pris en compte, celui-ci doit être le pseudo d'un utilisateur connecté. S'il n'en est pas un, le pseudo par défaut prend le dessus s'il existe dans le paramètre de l'action.  
Il existe également une commande à envoyer en privé au DongerBot pour que celui-ci répète sur le canal public la phrase passée en argument, exemple :  

    "!repeat XnS est vraiment stupide comme gars"

Structure du fichier json
-----
Le fichier json est décomposé de cette façon :
    
    ├ Catégorie
        ├  NomDonger
           ├ Action (action) : Message que Donger sort (not null)
           ├ Commande (commande) : Commande déclenchant Donger (not null)
           ├ Arguments (args): 1 (Pseudo), 2 (Texte), 3 (Spécial) (null)
           ├ Majuscules (caps) : true (not null if args)
           ├ Pseudo par défaut (default) : Pseudo (null)


Configuration
-----

La configuration est contenue dans le fichier dongerbot.py.


Archivage
-----

Les commandes exécutées en public et en privé sont repertoriées dans le dossier logs/ à la racine du dossier du Bot.

Changelog
-----
##### Version 2.1 - 20160920
- Ajout de la gestion des statistiques de chaque donger (!stats \<commande\>)
- Logging des commandes (absent dans version 2)

##### Version 2 - 20160916
- Refonte de la liste des actions
- Possibilité de blacklister un utilisateur par le bot (!blacklist, !unignore)
- Nouvelles commandes spéciales : !random, !friend, !who
- Suppression de la liste communiquée en privée
- Ajout d'un exemple de page listant la totalité des actions

##### Version 1 - 20160721
- Première version
