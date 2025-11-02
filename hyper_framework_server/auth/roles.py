from enum import Enum

class Permission(Enum):
    MANAGE_USERS = "MANAGE_USERS"
    DELETE_USERS = "DELETE_USERS"
    MANAGE_CONTROLS = "MANAGE_CONTROLS"
    EDIT_CONTROLS = "EDIT_CONTROLS"
    VIEW_CONTROLS = "VIEW_CONTROLS"
    DELETE_CONTROLS = "DELETE_CONTROLS"

class Role(Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    AUDITOR = "AUDITOR"

ROLE_PERMISSIONS = {
    Role.SUPER_ADMIN: {
        Permission.MANAGE_USERS, 
        Permission.DELETE_USERS,
        Permission.MANAGE_CONTROLS, 
        Permission.EDIT_CONTROLS, 
        Permission.VIEW_CONTROLS,
        Permission.DELETE_CONTROLS
    },
    Role.ADMIN: {
        Permission.MANAGE_USERS, 
        Permission.DELETE_USERS,
        Permission.MANAGE_CONTROLS, 
        Permission.VIEW_CONTROLS
    },
    Role.ANALYST: {
        Permission.VIEW_CONTROLS
    },
    Role.AUDITOR: set() 
}