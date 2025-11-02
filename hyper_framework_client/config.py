#---> CONTENU MODIFIÉ pour hyper_framework_client/config.py

import socket

def get_local_ip_address():
    """
    Détecte l'adresse IP locale principale de la machine sur le réseau.
    Se rabat sur '127.0.0.1' si aucune connexion réseau n'est trouvée.
    """
    try:
        # Crée un socket pour se connecter à une IP externe (sans envoyer de données)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Utilise une IP publique (DNS de Google), la connexion n'est pas réellement établie
        s.connect(("8.8.8.8", 80))
        # getsockname() retourne l'adresse IP locale utilisée pour cette "connexion"
        ip = s.getsockname()[0]
    except Exception:
        # En cas d'erreur (ex: pas de réseau), on utilise l'adresse de la machine locale
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# --- Configuration principale ---
# Le client détecte maintenant dynamiquement l'IP de la machine.
# Le fichier config.ini n'est plus nécessaire.

IP_ADDRESS = get_local_ip_address()
PORT = 5000
API_BASE_URL = f"http://{IP_ADDRESS}:{PORT}/api"

# Affiche l'URL utilisée pour confirmation (très utile pour le débogage)
print(f"Client configuré pour se connecter automatiquement à : {API_BASE_URL}")