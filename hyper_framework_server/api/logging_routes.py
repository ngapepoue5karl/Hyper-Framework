#---> FICHIER MODIFIÉ : hyper_framework_server/api/logging_routes.py

from flask import Blueprint, request, jsonify, current_app, Response
import os
import json
from ..auth.roles import Role
from ..services.logging_service import logging_service

bp = Blueprint('logging', __name__, url_prefix='/api/logs')

def _read_all_logs():
    """Lit et parse tous les fichiers .log du répertoire de logs."""
    log_dir = current_app.config['LOGS_DIR']
    all_logs = []
    if not os.path.exists(log_dir):
        return []
    
    log_files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')], reverse=True)
    
    for filename in log_files:
        filepath = os.path.join(log_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        all_logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue # Ignorer les lignes corrompues
        except IOError:
            continue # Ignorer les fichiers illisibles
            
    # Trier par timestamp descendant
    all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return all_logs

@bp.route('/', methods=['POST'])
def get_logs():
    data = request.get_json()
    requesting_username = data.get('username')
    
    # Nous loguons cette action avant de retourner les résultats
    logging_service.log_action(requesting_username, 'AUDIT_VIEW_LOGS', 'SUCCESS', {})

    if not requesting_username:
        return jsonify({'error': 'Authentification requise.'}), 401

    from ..database.database import get_db
    db = get_db()
    user = db.execute("SELECT role FROM users WHERE username = ?", (requesting_username,)).fetchone()

    if not user:
        return jsonify({'error': 'Utilisateur non valide.'}), 401

    requesting_role = Role(user['role'])
    all_logs = _read_all_logs()
    
    # Filtrage basé sur le rôle
    if requesting_role in [Role.SUPER_ADMIN, Role.AUDITOR]:
        return jsonify(all_logs)
    elif requesting_role == Role.ADMIN:
        allowed_roles = {Role.ANALYST.value, Role.AUDITOR.value}
        filtered_logs = [log for log in all_logs if log.get('user_role') in allowed_roles or log.get('username') == requesting_username]
        return jsonify(filtered_logs)
    else: # ANALYST et autres
        filtered_logs = [log for log in all_logs if log.get('username') == requesting_username]
        return jsonify(filtered_logs)

@bp.route('/export', methods=['GET'])
def export_logs():
    username = request.args.get('username', 'unknown')
    logging_service.log_action(username, 'AUDIT_EXPORT_LOGS', 'SUCCESS', {})
    
    all_logs = _read_all_logs()
    
    export_content = "\n".join([json.dumps(log, ensure_ascii=False) for log in all_logs])
    
    return Response(
        export_content,
        mimetype="text/plain",
        headers={"Content-disposition": "attachment; filename=hyper-framework-logs.txt"}
    )