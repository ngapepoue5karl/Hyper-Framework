#---> FICHIER MODIFIÉ : hyper_framework_server/api/auth_routes.py

from flask import Blueprint, request, jsonify
from ..auth import auth_service
from ..auth.exceptions import AuthException, UserNotFound
from ..auth.roles import Role
from ..database.database import get_db
from ..services.logging_service import logging_service

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    try:
        user = auth_service.login(username, data.get('password'))
        # Log de succès
        logging_service.log_action(username, 'USER_LOGIN', 'SUCCESS', {'message': 'Login successful'})
        return jsonify({
            'id': user.id, 'username': user.username, 'role': user.role.value,
            'is_temporary_password': user.is_temporary_password
        })
    except AuthException as e:
        # Log d'échec
        logging_service.log_action(username, 'USER_LOGIN', 'FAILURE', {'error': str(e)})
        return jsonify({'error': str(e)}), 401

@bp.route('/users', methods=['GET'])
def get_users():
    # --- AJOUT DE LA JOURNALISATION ---
    username = request.args.get('username', 'unknown')
    try:
        user_list = auth_service.get_all_users()
        logging_service.log_action(username, 'VIEW_USERS_LIST', 'SUCCESS', {'user_count': len(user_list)})
        return jsonify(user_list)
    except Exception as e:
        logging_service.log_action(username, 'VIEW_USERS_LIST', 'FAILURE', {'error': str(e)})
        return jsonify({'error': str(e)}), 500
    # --- FIN DE L'AJOUT ---

@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    # Note: L'utilisateur qui crée n'est pas dans le payload. Idéalement, il le serait.
    # Pour l'instant, on ne peut pas loguer "qui" a créé.
    try:
        temp_pass = auth_service.create_user(username, Role(data['role']))
        logging_service.log_action(username, 'USER_CREATE', 'SUCCESS', {'role': data['role']})
        return jsonify({'username': username, 'temporary_password': temp_pass}), 201
    except Exception as e:
        logging_service.log_action(username, 'USER_CREATE', 'FAILURE', {'error': str(e)})
        return jsonify({'error': str(e)}), 400

@bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Idéalement, le client enverrait le nom de l'utilisateur qui effectue l'action.
    try:
        auth_service.delete_user_by_id(user_id)
        logging_service.log_action('system', 'USER_DELETE', 'SUCCESS', {'deleted_user_id': user_id})
        return '', 204
    except Exception as e:
        logging_service.log_action('system', 'USER_DELETE', 'FAILURE', {'user_id': user_id, 'error': str(e)})
        return jsonify({'error': str(e)}), 400

@bp.route('/users/<int:user_id>/password', methods=['PUT'])
def update_password(user_id):
    data = request.get_json()
    try:
        auth_service.update_password(user_id, data['new_password'])
        logging_service.log_action('system', 'PASSWORD_UPDATE', 'SUCCESS', {'user_id': user_id})
        return jsonify({'message': 'Password updated successfully'})
    except Exception as e:
        logging_service.log_action('system', 'PASSWORD_UPDATE', 'FAILURE', {'user_id': user_id, 'error': str(e)})
        return jsonify({'error': str(e)}), 400

@bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    current_username = data.get('current_username')
    if not current_username:
        return jsonify({'error': 'Le nom de l\'utilisateur courant est requis pour l\'autorisation.'}), 401
    try:
        db = get_db()
        user = db.execute("SELECT role FROM users WHERE username = ?", (current_username,)).fetchone()
        if not user:
            return jsonify({'error': 'Utilisateur courant non valide.'}), 401
        current_user_role = Role(user['role'])

        auth_service.update_user(user_id, current_user_role, data.get('username'), data.get('role'))
        logging_service.log_action(current_username, 'USER_UPDATE', 'SUCCESS', {'updated_user_id': user_id, 'changes': data})
        return jsonify({'message': 'Utilisateur mis à jour avec succès.'})
    except (ValueError, UserNotFound) as e:
        logging_service.log_action(current_username, 'USER_UPDATE', 'FAILURE', {'updated_user_id': user_id, 'error': str(e)})
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logging_service.log_action(current_username, 'USER_UPDATE', 'FAILURE', {'updated_user_id': user_id, 'error': str(e)})
        return jsonify({'error': str(e)}), 400