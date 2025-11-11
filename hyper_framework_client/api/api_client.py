#---> CONTENU MODIFIÉ pour hyper_framework_client/api/api_client.py

import requests
from ..config import API_BASE_URL
import json

class ApiClient:
    def _make_request(self, method, url, **kwargs):
        """
        Méthode centralisée pour effectuer des requêtes et gérer les erreurs réseau.
        """
        try:
            response = requests.request(method, url, **kwargs)
            return self._handle_response(response)
        except requests.exceptions.ConnectionError:
            raise Exception("Erreur de connexion : Impossible de joindre le serveur. Vérifiez qu'il est bien démarré et accessible.")
        except requests.exceptions.Timeout:
            raise Exception("Le serveur a mis trop de temps à répondre (timeout).")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Une erreur réseau est survenue : {e}")

    def _handle_response(self, response):
        if response.ok and response.headers.get('Content-Type', '').startswith('text/plain'):
            return response.text
        if response.ok and response.headers.get('Content-Type', '').startswith('text/csv'):
            return response.text
        if not response.ok:
            try:
                error_data = response.json()
                raise Exception(error_data.get('error', f"Erreur API : {response.status_code}"))
            except (ValueError, json.JSONDecodeError):
                raise Exception(f"Erreur API : {response.status_code} - {response.text}")
        if response.status_code == 204:
            return None
        if not response.text or not response.text.strip():
            return []
        try:
            return response.json()
        except json.JSONDecodeError:
            raise Exception(f"La réponse du serveur n'était pas un JSON valide. Contenu reçu : {response.text[:200]}")

    def login(self, username, password):
        return self._make_request('post', f"{API_BASE_URL}/auth/login", json={'username': username, 'password': password})

    def get_all_users(self, username):
        return self._make_request('get', f"{API_BASE_URL}/auth/users?username={username}")

    def create_user(self, username, role_value):
        return self._make_request('post', f"{API_BASE_URL}/auth/users", json={'username': username, 'role': role_value})
        
    def delete_user(self, user_id):
        return self._make_request('delete', f"{API_BASE_URL}/auth/users/{user_id}")

    def update_password(self, user_id, new_password):
        return self._make_request('put', f"{API_BASE_URL}/auth/users/{user_id}/password", json={'new_password': new_password})

    def update_user(self, user_id, current_username, new_username, new_role):
        payload = {'current_username': current_username}
        if new_username: payload['username'] = new_username
        if new_role: payload['role'] = new_role
        if len(payload) <= 1: raise ValueError("Aucune donnée à mettre à jour.")
        return self._make_request('put', f"{API_BASE_URL}/auth/users/{user_id}", json=payload)

    def get_all_controls(self, username):
        return self._make_request('get', f"{API_BASE_URL}/controls?username={username}")

    def get_control_details(self, control_id, username):
        return self._make_request('get', f"{API_BASE_URL}/controls/{control_id}?username={username}")
        
    def create_control(self, name, desc, code, user):
        payload = {'name': name, 'description': desc, 'script_code': code, 'username': user}
        return self._make_request('post', f"{API_BASE_URL}/controls", json=payload)
    
    def update_control(self, ctrl_id, name, desc, code, user):
        payload = {'name': name, 'description': desc, 'script_code': code, 'username': user}
        return self._make_request('put', f"{API_BASE_URL}/controls/{ctrl_id}", json=payload)

    def delete_control(self, control_id, username):
        return self._make_request('delete', f"{API_BASE_URL}/controls/{control_id}", json={'username': username})    

    def execute_control(self, control_id, files_dict, data_dict):
        url = f"{API_BASE_URL}/controls/{control_id}/execute"
        return self._make_request('post', url, files=files_dict, data=data_dict)
        
    def get_result_file_content(self, filename):
        return self._make_request('get', f"{API_BASE_URL}/results/{filename}")

    def execute_and_generate_report(self, control_id, files_dict, data_dict):
        url = f"{API_BASE_URL}/reports/execute-and-generate"
        data_with_id = {'control_id': control_id, **data_dict}
        return self._make_request('post', url, files=files_dict, data=data_with_id)

    def get_logs(self, username):
        return self._make_request('post', f"{API_BASE_URL}/logs/", json={'username': username})

    def export_logs(self, username):
        return self._make_request('get', f"{API_BASE_URL}/logs/export?username={username}")

    def download_report(self, filename, username):
        url = f"{API_BASE_URL}/reports/download/{filename}?username={username}"
        return requests.get(url, stream=True, timeout=120)

    def get_analysis_runs(self, username):
        """Récupère la liste de toutes les analyses exécutées"""
        return self._make_request('get', f"{API_BASE_URL}/analysis-runs?username={username}")

    def get_analysis_run_details(self, run_id, username):
        """Récupère les détails d'une analyse exécutée"""
        return self._make_request('get', f"{API_BASE_URL}/analysis-runs/{run_id}?username={username}")

api_client = ApiClient()