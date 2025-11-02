#---> FICHIER MODIFIÉ : run_application.py

import subprocess
import sys
import time
import atexit

# Garder une référence au processus serveur pour pouvoir le terminer
server_process = None

def start_server():
    """Lance le serveur Flask dans un processus séparé."""
    global server_process
    print("Starting Flask server in a separate process...")
    # Utilise 'python -m' pour s'assurer que les imports relatifs fonctionnent
    command = [sys.executable, "-m", "hyper_framework_server.run_server"]
    server_process = subprocess.Popen(command)
    print(f"Server process started with PID: {server_process.pid}")

def start_client():
    """Lance l'application client Tkinter."""
    print("Launching GUI Client...")
    # On importe ici pour éviter les imports circulaires ou précoces
    from hyper_framework_client.ui.login_window import LoginWindow
    app = LoginWindow()
    app.mainloop()

def cleanup():
    """Fonction pour arrêter le serveur à la fermeture."""
    global server_process
    if server_process and server_process.poll() is None:
        print("Terminating server process...")
        server_process.terminate()
        server_process.wait()
        print("Server process terminated.")

if __name__ == '__main__':
    # Enregistre la fonction de nettoyage pour qu'elle soit appelée à la sortie
    atexit.register(cleanup)

    try:
        start_server()
        # Laisse un peu de temps au serveur pour démarrer
        time.sleep(3)
        start_client()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # cleanup() sera appelé automatiquement par atexit
        print("Application closing.")