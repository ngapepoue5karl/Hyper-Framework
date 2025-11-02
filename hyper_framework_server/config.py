#---> FICHIER MODIFIÉ : hyper_framework_server/config.py

import os
from pathlib import Path

# --- Étape 1: Définir tous les chemins en utilisant des objets Path ---

# Le chemin racine du package serveur
SERVER_ROOT = Path(__file__).resolve().parent

# Dossier principal pour les données modifiables par l'utilisateur
_APP_DATA_DIR = SERVER_ROOT / "data"

# Base de données
_DB_FILE = _APP_DATA_DIR / "hyper_framework_server.db"

# Dossiers de données
_SCRIPTS_DIR = _APP_DATA_DIR / "scripts"
_INPUTS_DIR = _APP_DATA_DIR / "inputs"
_OUTPUTS_DIR = _APP_DATA_DIR / "outputs"
_REPORTS_DIR = _APP_DATA_DIR / "reports"
_LOGS_DIR = _APP_DATA_DIR / "logs" # <-- NOUVEAU


# Dossier pour les assets internes par défaut (non modifiables)
DEFAULT_ASSETS_DIR = SERVER_ROOT / "assets"


# --- Étape 2: Créer tous les dossiers nécessaires ---

# Liste des dossiers à créer
dirs_to_create = [
    _APP_DATA_DIR,
    _SCRIPTS_DIR,
    _INPUTS_DIR,
    _OUTPUTS_DIR,
    _REPORTS_DIR,
    _LOGS_DIR # <-- NOUVEAU
]

for dir_path in dirs_to_create:
    os.makedirs(dir_path, exist_ok=True)


# --- Étape 3: Exporter les chemins en tant que chaînes de caractères (str) ---
# Le reste de l'application utilisera ces variables.

DB_FILE = str(_DB_FILE)
SCRIPTS_DIR = str(_SCRIPTS_DIR)
INPUTS_DIR = str(_INPUTS_DIR)
OUTPUTS_DIR = str(_OUTPUTS_DIR)
REPORTS_DIR = str(_REPORTS_DIR)
LOGS_DIR = str(_LOGS_DIR) # <-- NOUVEAU

# Timeout pour l'exécution des scripts
SCRIPT_EXECUTION_TIMEOUT = 30