#---> CONTENU MODIFIÉ pour hyper_framework_client/auth_roles.py

from enum import Enum

class Permission(Enum):
    MANAGE_USERS = "MANAGE_USERS"
    DELETE_USERS = "DELETE_USERS"
    VIEW_USERS = "VIEW_USERS"
    MANAGE_CONTROLS = "MANAGE_CONTROLS"
    EDIT_CONTROLS = "EDIT_CONTROLS"
    VIEW_CONTROLS = "VIEW_CONTROLS"
    DELETE_CONTROLS = "DELETE_CONTROLS"
    VIEW_LOGS = "VIEW_LOGS"  # --- AJOUT DE LA NOUVELLE PERMISSION ---

class Role(Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    AUDITOR = "AUDITOR"

ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: {
        Permission.MANAGE_USERS,
        Permission.DELETE_USERS,
        Permission.VIEW_USERS,
        Permission.MANAGE_CONTROLS,
        Permission.EDIT_CONTROLS,
        Permission.VIEW_CONTROLS,
        Permission.DELETE_CONTROLS,
        Permission.VIEW_LOGS  # --- AJOUT ICI ---
    },
    Role.ADMIN: {
        Permission.MANAGE_USERS,
        Permission.DELETE_USERS,
        Permission.VIEW_USERS,
        Permission.MANAGE_CONTROLS,
        Permission.VIEW_CONTROLS,
        Permission.EDIT_CONTROLS,
        Permission.DELETE_CONTROLS,
        Permission.VIEW_LOGS  # --- AJOUT ICI ---
    },
    Role.ANALYST: {
        Permission.VIEW_CONTROLS,
        Permission.VIEW_USERS
    },
    # L'Auditor n'a aucune permission fonctionnelle
    Role.AUDITOR: set()
}