#---> FICHIER MODIFIÉ : hyper_framework_server/services/logging_service.py

from flask import request, current_app
import json
from datetime import datetime
import os
import threading
from ..database.database import get_db

class FileLoggingService:
    def __init__(self):
        self._lock = threading.Lock()

    def log_action(self, username, action, status, details=None):
        """
        Enregistre une action utilisateur dans un fichier log journalier.
        """
        try:
            with self._lock:
                # Obtenir le rôle de l'utilisateur (on a toujours besoin de la DB pour ça)
                db = get_db()
                user = db.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()
                user_role = user['role'] if user else "N/A"
                
                # Construire l'entrée de log
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "username": username,
                    "user_role": user_role,
                    "ip_address": request.remote_addr if request else "N/A", # Gérer le cas hors contexte de requête
                    "action": action,
                    "status": status,
                    "details": details or {}
                }

                # Déterminer le fichier de log
                log_dir = current_app.config['LOGS_DIR']
                today_str = datetime.now().strftime('%Y-%m-%d')
                log_file_path = os.path.join(log_dir, f"{today_str}.log")

                # Écrire dans le fichier
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry) + '\n')

        except Exception as e:
            # Ne pas faire échouer la requête principale si le logging échoue
            print(f"CRITICAL: Failed to log action to file. Error: {e}")

logging_service = FileLoggingService()