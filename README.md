# Hyper-Framework

**Hyper-Framework** est une plateforme client-serveur sécurisée conçue pour standardiser, automatiser et tracer l'exécution d'analyses de données. Elle permet à des analystes et auditeurs de lancer des scripts d'analyse (appelés "Contrôles") sur des fichiers de données via une interface de bureau conviviale, tout en offrant aux administrateurs un contrôle total sur les utilisateurs, les permissions et les scripts autorisés.

## Table des Matières
1.  [Architecture](#1-architecture)
    *   [Architecture Globale](#architecture-globale)
    *   [Structure des Dossiers](#structure-des-dossiers)
    *   [Flux de Données Typique](#flux-de-données-typique)
2.  [Fonctionnalités et Utilité](#2-fonctionnalités-et-utilité)
3.  [Guide d'Utilisation](#3-guide-dutilisation)
    *   [Connexion](#connexion)
    *   [Lancer une Analyse](#lancer-une-analyse)
    *   [Gestion des Contrôles (Admins)](#gestion-des-contrôles-admins)
    *   [Gestion des Utilisateurs (Admins)](#gestion-des-utilisateurs-admins)
    *   [Journal d'Activité](#journal-dactivité)
4.  [Commandes et Lancement (Développement)](#4-commandes-et-lancement-développement)
    *   [Prérequis](#prérequis)
    *   [Installation](#installation)
    *   [Lancement de l'Application](#lancement-de-lapplication)
5.  [Guide de Déploiement](#5-guide-de-déploiement)
    *   [Déploiement du Serveur](#déploiement-du-serveur)
    *   [Création de l'Installateur Client](#création-de-linstallateur-client)

---

## 1. Architecture

### Architecture Globale

Le projet est basé sur une architecture Client-Serveur découplée :

*   **Serveur (Backend)**
    *   **Technologie** : Python avec le micro-framework **Flask**.
    *   **Rôle** : Cerveau de l'application. Il expose une API RESTful pour toutes les opérations.
    *   **Responsabilités** :
        *   Authentification et gestion des sessions utilisateur.
        *   Gestion des utilisateurs et de leurs rôles (CRUD).
        *   Stockage et gestion des "Contrôles" (scripts Python).
        *   Exécution sécurisée et isolée des scripts d'analyse.
        *   Interaction avec la base de données (SQLite).
        *   Génération de rapports (DOCX) et journalisation de toutes les actions.
    *   **Service web** : Utilise **Waitress** comme serveur de production WSGI léger.

*   **Client (Frontend)**
    *   **Technologie** : Python avec la bibliothèque **CustomTkinter** pour l'interface graphique.
    *   **Rôle** : Interface utilisateur de bureau (Rich Client).
    *   **Responsabilités** :
        *   Fournir une interface de connexion sécurisée.
        *   Permettre aux utilisateurs de naviguer, sélectionner et exécuter des analyses.
        *   Gérer le chargement des fichiers de données par l'utilisateur.
        *   Afficher les résultats renvoyés par le serveur de manière structurée (tableaux, statistiques).
        *   Fournir des interfaces de gestion pour les administrateurs (utilisateurs, contrôles).
        *   Télécharger les rapports et les logs générés par le serveur.

*   **Communication**
    *   Le client communique exclusivement avec le serveur via des requêtes HTTP sur son API REST.
    *   Les données sont échangées au format JSON. Les fichiers sont envoyés via des requêtes `multipart/form-data`.

### Structure des Dossiers

```
distributable_v4/
├── hyper_framework_client/         # Code source du client
│   ├── api/                        # Module pour communiquer avec l'API du serveur
│   ├── ui/                         # Tous les composants graphiques (fenêtres, frames)
│   ├── app.py                      # Point d'entrée du client
│   └── config.py                   # Configuration client (détection auto de l'IP)
│
├── hyper_framework_server/         # Code source du serveur
│   ├── api/                        # Définition des routes de l'API (endpoints)
│   ├── auth/                       # Logique d'authentification et gestion des rôles
│   ├── database/                   # Gestion de la base de données SQLite
│   ├── services/                   # Logique métier (exécution de script, rapports, logs)
│   ├── data/                       # Données du serveur (DB, scripts, logs, rapports)
│   │   ├── hyper_framework_server.db
│   │   ├── scripts/
│   │   ├── logs/
│   │   └── reports/
│   ├── app.py                      # Création de l'application Flask
│   └── run_server.py               # Script pour lancer le serveur Waitress
│
├── run_application.py              # Script principal pour lancer serveur + client en mode dév
├── HyperFrameworkClient.spec       # Fichier de configuration pour PyInstaller
└── setup_client.iss                # Fichier de configuration pour Inno Setup
```

### Flux de Données Typique

1.  L'utilisateur lance le client et se connecte.
2.  Le client envoie les identifiants à l'endpoint `/api/auth/login` du serveur.
3.  Le serveur vérifie les identifiants dans sa base de données SQLite et renvoie les informations de l'utilisateur (rôle, permissions).
4.  Le client affiche l'interface principale, adaptée aux permissions de l'utilisateur.
5.  L'utilisateur sélectionne un "Contrôle" et charge les fichiers de données requis.
6.  Le client envoie l'ID du contrôle et les fichiers à l'endpoint `/api/controls/<id>/execute`.
7.  Le serveur stocke temporairement les fichiers, récupère le script Python associé au contrôle et l'exécute.
8.  Le script (utilisant Pandas) traite les données et retourne une structure de résultats (dictionnaires, DataFrames).
9.  Le serveur formate les résultats en JSON et les renvoie au client.
10. Le client reçoit le JSON et affiche les résultats dans des tableaux et des fiches de synthèse.
11. Chaque action majeure (connexion, exécution, création d'utilisateur) est enregistrée dans un fichier de log journalier par le serveur.

---

## 2. Fonctionnalités et Utilité

Ce framework est particulièrement utile dans des contextes d'audit, de contrôle interne ou d'analyse de données récurrente où la traçabilité, la sécurité et la standardisation sont primordiales.

*   **Gestion centralisée des analyses** : Tous les scripts sont stockés et versionnés sur le serveur, garantissant que tous les analystes utilisent la même logique.
*   **Sécurité des scripts** : Avant de sauvegarder un script, le serveur l'analyse via un AST (Abstract Syntax Tree) pour interdire les modules et fonctions dangereux (`os.system`, `subprocess`, `eval`, etc.), prévenant l'exécution de code malveillant.
*   **Gestion fine des utilisateurs et des rôles** :
    *   **SUPER_ADMIN** : Contrôle total sur tout.
    *   **ADMIN** : Peut gérer les utilisateurs (sauf autres admins) et les contrôles.
    *   **ANALYST** : Peut uniquement voir et exécuter les contrôles.
    *   **AUDITOR** : Accès restreint, peut consulter les logs.
*   **Exécution d'analyse simplifiée** : L'interface guide l'utilisateur pour charger les bons fichiers et lancer l'analyse en un clic, sans avoir besoin de manipuler du code ou des environnements Python.
*   **Traçabilité complète (Audit Trail)** : Le service de journalisation enregistre qui a fait quoi, quand, et avec quel résultat. Les logs sont consultables et exportables depuis l'interface.
*   **Génération de rapports automatique** : Après chaque analyse, l'utilisateur peut générer un rapport professionnel au format DOCX contenant les statistiques clés et les tableaux de résultats, prêt à être partagé.
*   **Configuration client simplifiée** : Le client n'a plus besoin de fichier `config.ini`. Il détecte automatiquement l'adresse IP de la machine sur laquelle il est lancé, simplifiant le déploiement.

---

## 3. Guide d'Utilisation

### Connexion
1.  Lancez l'exécutable `HyperFrameworkClient.exe`.
2.  Saisissez votre nom d'utilisateur et votre mot de passe.
3.  Si c'est votre première connexion, un mot de passe temporaire vous a été fourni. L'application vous demandera de le changer immédiatement.

### Lancer une Analyse
1.  L'écran d'accueil ("Accueil") affiche la liste de toutes les analyses (Contrôles) disponibles.
2.  Utilisez la barre de recherche pour filtrer la liste par nom ou description.
3.  Sélectionnez une analyse dans la liste et cliquez sur **"Lancer l'Analyse Sélectionnée"**.
4.  L'écran d'analyse s'affiche. Sur la gauche, cliquez sur les boutons **"Charger..."** pour chaque fichier requis.
5.  Une fois tous les fichiers chargés, cliquez sur **"Lancer l'Analyse"**.
6.  Les résultats s'afficheront dans la partie droite de la fenêtre.
7.  Une fois l'analyse terminée, vous pouvez :
    *   **"Exporter (Excel)"** : Sauvegarde tous les tableaux de résultats dans un unique fichier Excel.
    *   **"Générer et Télécharger (DOCX)"** : Crée un rapport Word complet et vous invite à le sauvegarder.

### Gestion des Contrôles (Admins)
1.  Dans le menu de gauche, cliquez sur **"Gestion Contrôles"**.
2.  **Créer** : Cliquez sur "Créer un Contrôle", remplissez le nom, la description et collez votre code Python dans l'éditeur. Un modèle de script est fourni pour vous guider.
3.  **Éditer** : Sélectionnez un contrôle dans la liste et cliquez sur "Éditer".
4.  **Supprimer** : Sélectionnez un contrôle et cliquez sur "Supprimer".

### Gestion des Utilisateurs (Admins)
1.  Dans le menu de gauche, cliquez sur **"Gestion Utilisateurs"**.
2.  La partie droite est dédiée à la création. Remplissez le nom d'utilisateur, choisissez un rôle, et cliquez sur **"Créer Utilisateur"**. Un mot de passe temporaire sera affiché. **Notez-le et transmettez-le de manière sécurisée.**
3.  Pour modifier ou supprimer un utilisateur, sélectionnez-le dans la liste de gauche. Les options "Mettre à jour" et "Supprimer" deviendront actives.

### Journal d'Activité
1.  Cliquez sur **"Journal d'Activité"** dans le menu.
2.  La liste des logs s'affiche, triée du plus récent au plus ancien.
3.  Cliquez sur **"Exporter les Logs"** pour sauvegarder l'intégralité des journaux dans un fichier texte.

---

## 4. Commandes et Lancement (Développement)

### Prérequis
*   Python 3.8+
*   Git (optionnel)

### Installation
1.  Clonez le dépôt ou décompressez l'archive.
2.  Ouvrez deux terminaux.
3.  Dans le premier terminal, installez les dépendances du serveur :
    ```bash
    cd /chemin/vers/distributable_v4/hyper_framework_server
    pip install -r requirements.txt
    ```
4.  Dans le second terminal, installez les dépendances du client :
    ```bash
    cd /chemin/vers/distributable_v4/hyper_framework_client
    pip install -r requirements.txt
    ```

### Lancement de l'Application
Le script `run_application.py` à la racine est conçu pour lancer le serveur et le client simultanément pour le développement.

1.  Placez-vous à la racine du projet (`distributable_v4`).
2.  Exécutez la commande suivante :
    ```bash
    python run_application.py
    ```
3.  Cela va :
    *   Démarrer le serveur Flask/Waitress dans un processus d'arrière-plan. L'adresse IP du serveur sera affichée dans la console.
    *   Attendre 3 secondes pour que le serveur s'initialise.
    *   Lancer l'interface graphique du client.
4.  Pour arrêter l'ensemble, fermez la fenêtre du client. Le script `run_application.py` interceptera la fermeture et arrêtera proprement le processus du serveur.

---

## 5. Guide de Déploiement

### Déploiement du Serveur
Le serveur est une application Flask autonome. Il doit être déployé sur une machine ou un serveur accessible par les clients sur le réseau local.

1.  Copiez le dossier `hyper_framework_server` sur la machine cible.
2.  Assurez-vous que Python est installé sur cette machine.
3.  Installez les dépendances : `pip install -r requirements.txt`.
4.  Lancez le serveur avec la commande suivante. Il tournera indéfiniment jusqu'à ce que vous arrêtiez le processus (Ctrl+C).
    ```bash
    python -m hyper_framework_server.run_server
    ```
5.  La console affichera l'adresse IP que les clients doivent utiliser pour se connecter. **Notez cette adresse IP.**

### Création de l'Installateur Client
L'objectif est de créer un fichier `Setup.exe` unique que vous pouvez distribuer aux utilisateurs finaux.

**Prérequis** :
*   **PyInstaller** : Pour convertir le script Python du client en un exécutable `.exe`.
    ```bash
    pip install pyinstaller
    ```
*   **Inno Setup Compiler** : Un outil gratuit pour Windows pour créer des installateurs. [Téléchargez-le ici](https://jrsoftware.org/isinfo.php).

**Étapes** :

1.  **Générer l'exécutable** :
    *   Ouvrez un terminal à la racine du projet (`distributable_v4`).
    *   Exécutez PyInstaller avec le fichier de spécification fourni :
        ```bash
        pyinstaller HyperFrameworkClient.spec
        ```
    *   Cette commande va créer un dossier `dist/HyperFrameworkClient` contenant tous les fichiers nécessaires à l'exécution de l'application.

2.  **Compiler l'installateur** :
    *   Ouvrez **Inno Setup Compiler**.
    *   Allez dans `File > Open...` et sélectionnez le fichier `setup_client.iss` à la racine du projet.
    *   Allez dans `Build > Compile` (ou appuyez sur F9).
    *   Inno Setup va prendre le contenu du dossier `dist/HyperFrameworkClient` et le compresser dans un seul fichier d'installation nommé `Setup_HyperFramework_Client_v1.0.exe` (le nom est défini dans le script `.iss`). Ce fichier sera généré dans un sous-dossier `Output`.

3.  **Distribution** :
    *   Distribuez le fichier `Setup_HyperFramework_Client_v1.0.exe` aux utilisateurs. Ils n'ont qu'à double-cliquer dessus pour installer le client sur leur machine. L'application sera accessible depuis le Menu Démarrer et/ou le bureau.