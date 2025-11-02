from .roles import Role, Permission, ROLE_PERMISSIONS

class User:
    def __init__(self, username: str, role: Role, is_temporary_password: bool, password_hash: str = None, user_id: int = None):
        self.id = user_id
        self.username = username
        self.role = role
        self.is_temporary_password = is_temporary_password
    
    def has_permission(self, permission: Permission) -> bool:
        user_permissions = ROLE_PERMISSIONS.get(self.role, set())
        return permission in user_permissions
