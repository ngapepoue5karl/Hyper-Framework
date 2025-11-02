import bcrypt, string, random
from ..database.database import get_db
from .models import User
from .roles import Role
from .exceptions import UserNotFound, InvalidPassword, WeakPassword, UserAlreadyExists, AuthException
import pandas as pd
import io



def _hash_password(p): return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt())
def _check_password(p, h): return bcrypt.checkpw(p.encode('utf-8'), h)

def login(username, password):
    db = get_db()
    user_data = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    
    # --- MODIFICATION DE LA LOGIQUE D'ERREUR ---
    # Au lieu de retourner des erreurs spécifiques, on retourne une erreur générique
    # pour des raisons de sécurité (empêche l'énumération des utilisateurs).
    if not user_data or not _check_password(password, user_data['password_hash']):
        raise AuthException("Nom ou mot de passe incorrect.")
    # --- FIN DE LA MODIFICATION ---
    
    return User(user_id=user_data['id'], username=user_data['username'], role=Role(user_data['role']), is_temporary_password=bool(user_data['is_temporary_password']))

def create_user(username, role):
    if role == Role.SUPER_ADMIN: raise ValueError("Cannot create another SUPER_ADMIN.")
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    db = get_db()
    if db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone(): raise UserAlreadyExists(f"User '{username}' already exists.")
    db.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",(username, _hash_password(temp_password), role.value))
    db.commit()
    return temp_password

def get_all_users():
    db = get_db()
    users_data = db.execute("SELECT id, username, role FROM users").fetchall()
    return [{'id': r['id'], 'username': r['username'], 'role': r['role']} for r in users_data]

def delete_user_by_id(user_id):
    db = get_db()
    user = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user: raise UserNotFound("User not found.")
    if Role(user['role']) == Role.SUPER_ADMIN: raise ValueError("SUPER_ADMIN cannot be deleted.")
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()

def update_password(user_id, new_password):
    if len(new_password) < 8: raise WeakPassword("Password must be at least 8 chars.")
    db = get_db()
    db.execute("UPDATE users SET password_hash = ?, is_temporary_password = 0 WHERE id = ?", (_hash_password(new_password), user_id))
    db.commit()

def update_user(user_id, current_user_role: Role, new_username=None, new_role_str=None):
    """Met à jour le nom et/ou le rôle d'un utilisateur avec des vérifications de sécurité."""
    if not new_username and not new_role_str:
        raise ValueError("Aucune information de mise à jour fournie (nom ou rôle).")

    db = get_db()
    user_to_update = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user_to_update:
        raise UserNotFound("L'utilisateur à mettre à jour n'a pas été trouvé.")
    
    target_user_role = Role(user_to_update['role'])
    
    # Règle 1: Personne ne peut modifier le SUPER_ADMIN
    if target_user_role == Role.SUPER_ADMIN:
        raise ValueError("Impossible de modifier les informations du SUPER_ADMIN.")
        
    # Règle 2: Un ADMIN ne peut pas modifier un autre ADMIN
    if current_user_role == Role.ADMIN and target_user_role == Role.ADMIN:
        raise ValueError("Un Administrateur ne peut pas modifier les informations d'un autre Administrateur.")

    update_clauses = []
    params = []

    if new_username:
        existing = db.execute("SELECT id FROM users WHERE username = ? AND id != ?", (new_username, user_id)).fetchone()
        if existing:
            raise UserAlreadyExists(f"Le nom d'utilisateur '{new_username}' existe déjà.")
        update_clauses.append("username = ?")
        params.append(new_username)

    if new_role_str:
        try:
            new_role = Role(new_role_str)
            if new_role == Role.SUPER_ADMIN:
                raise ValueError("Impossible d'assigner le rôle SUPER_ADMIN.")
            # Un ADMIN ne peut pas promouvoir quelqu'un en ADMIN
            if current_user_role == Role.ADMIN and new_role == Role.ADMIN:
                 raise ValueError("Seul un SUPER_ADMIN peut assigner le rôle Administrateur.")
            update_clauses.append("role = ?")
            params.append(new_role.value)
        except ValueError as e:
            raise ValueError(f"Rôle invalide : {new_role_str}. {e}")

    if not update_clauses:
        return

    params.append(user_id)
    query = f"UPDATE users SET {', '.join(update_clauses)} WHERE id = ?"
    
    db.execute(query, tuple(params))
    db.commit()

def _update_superadmin_password():
    db = get_db()
    db.execute("UPDATE users SET password_hash = ? WHERE username = 'superadmin'", (_hash_password("superadmin"),))
    db.commit()

def _update_superadmin_password_from_db_instance(db):
    db.execute("UPDATE users SET password_hash = ? WHERE username = 'superadmin'", (_hash_password("superadmin"),))
    db.commit()

def _update_superadmin_password():
    db = get_db()
    _update_superadmin_password_from_db_instance(db)