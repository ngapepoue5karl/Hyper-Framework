#---> CONTENU MODIFIÉ pour hyper_framework_client/app.py

import sys
import os

# --- Début du correctif pour PyInstaller et l'exécution directe ---
# Ajoute le répertoire parent (la racine du projet) au chemin de recherche de Python.
# Cela permet aux imports absolus comme "from hyper_framework_client..." de fonctionner.
try:
    # Obtient le chemin du dossier contenant app.py (hyper_framework_client)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Obtient le chemin du dossier parent (la racine du projet)
    project_root = os.path.dirname(current_dir)
    # Ajoute la racine du projet au sys.path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    # Fallback pour certains environnements où __file__ n'est pas défini
    if '.' not in sys.path:
        sys.path.insert(0, '.')
# --- Fin du correctif ---


# Maintenant, nous pouvons utiliser un import absolu, ce qui est plus robuste
from hyper_framework_client.ui.login_window import LoginWindow

def main():
    """Point d'entrée de l'application client."""
    app = LoginWindow()
    app.mainloop()

if __name__ == "__main__":
    main()