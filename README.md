# 🪱 WORMS Like -- Projet Python-Maths (3A DJV)

Ce projet est une réinterprétation simplifiée du célèbre jeu **Worms**,
développée en **Python** avec la librairie **Pygame**.\
L'objectif est de programmer un jeu au tour par tour dans lequel des
personnages s'affrontent à l'aide d'armes soumises à des lois physiques.

## 🎯 Objectif du jeu

Deux joueurs (ou plus) s'affrontent sur un terrain en 2D vu de profil.\
Chaque joueur contrôle un ou plusieurs personnages, se déplaçant et
tirant différents projectiles pour éliminer l'adversaire.

La partie se termine lorsqu'un seul joueur possède encore des
personnages en vie.

## 🧩 Fonctionnalités principales

### ✔️ Fonctionnalités minimales

-   2 joueurs\
-   1 personnage par joueur\
-   Terrain horizontal indestructible\
-   Déplacements du personnage : marche et saut\
-   2 armes :
    -   **Grenade** : soumise à la gravité, explose à l'impact\
    -   **Roquette** : soumise à la gravité et au vent, explose à
        l'impact\
-   Les explosions tuent instantanément tout personnage dans leur rayon

## ⭐ Fonctionnalités avancées (modifiable selon vos ajouts)

-   Timer de la grenade\
-   Aire d'effet réaliste\
-   Souffle des explosions\
-   Vent variable\
-   Plusieurs personnages par joueur\
-   Plus de 2 joueurs\
-   Terrain destructible\
-   Autres armes\
-   Effets sonores\
-   Génération de niveaux

## 🎮 Contrôles (exemple)

  Action           Touche
  ---------------- --------
  Gauche           ←
  Droite           →
  Saut             Espace
  Tirer            Entrée
  Changer d'arme   A

## 🛠️ Installation

``` bash
pip install pygame
python main.py
```

## 📁 Structure du projet

    WormsLike/
    │── main.py
    │── game.py
    │── terrain.py
    │── player.py
    │── character.py
    │── weapons/
    │── assets/
    │── utils/
    │── README.md

## 👥 Équipe

(À compléter)
