#---> CONTENU MODIFIÉ pour hyper_framework_server/run_server.py

from .app import create_app
from waitress import serve
import socket

# Crée l'application Flask
app = create_app()

def get_ip_address():
    try:
        # Tente de se connecter à une IP externe pour trouver l'IP locale
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == '__main__':
    host = '0.0.0.0' # Écoute sur toutes les interfaces réseau
    port = 5000
    local_ip = get_ip_address()
    
    print("===================================================")
    print("     Démarrage du Serveur Hyper-Framework")
    print("===================================================")
    print(f" Le serveur est accessible sur votre réseau local.")
    print(f" -> Configurez le client avec l'adresse IP : {local_ip}")
    print(f" -> URL complète pour le client : http://{local_ip}:{port}/api")
    print("===================================================")
    print("Pour arrêter le serveur, appuyez sur CTRL+C.")
    
    # Utilisation de Waitress pour un environnement de production léger
    serve(app, host=host, port=port)