class AuthException(Exception): pass
class UserNotFound(AuthException): pass
class InvalidPassword(AuthException): pass
class WeakPassword(AuthException): pass
class UserAlreadyExists(AuthException): pass
