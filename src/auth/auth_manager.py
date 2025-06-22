import bcrypt
import jwt
import datetime
import secrets
import re
from typing import Dict, Optional, Tuple

from ..database import get_db


JWT_SECRET = secrets.token_hex(32)  # Генерация рандомного токена
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24 * 60 * 60  #Валидность 24 часа


class AuthManager:

    @staticmethod
    def hash_password(password: str) -> str:
        """Хешеруем пароль ."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Верификация пароля по hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        Возвращаем кортеж (is_valid, message).
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one digit"

        if not re.search(r"[!@#$%^&*(),.?:{}|<>]", password):
            return False, "Password must contain at least one special character"

        return True, "Password is strong" #Соблюдаем условия безопасности

    @staticmethod
    def validate_email(email: str) -> bool:
        """Валидация email,но в проекте SMPT не реализован."""
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(email_pattern, email))

    @staticmethod
    def generate_token(user_id: int, role: str) -> str:
        """Генерация токена JWT юзера"""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRATION)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """Чекаем JWT токен на валидность"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def register_user(username: str, email: str, password: str, first_name: str,
                      last_name: str, role: str = 'employee') -> Tuple[bool, str, Optional[int]]:
        """
        Регистрация юзера
       Возвращаем кортеж (success, message, user_id).
        """
        db = get_db()

        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters long", None

        if not AuthManager.validate_email(email):
            return False, "Invalid email format", None

        valid_password, password_message = AuthManager.validate_password_strength(password)
        if not valid_password:
            return False, password_message, None

        if role not in ['employee', 'employer', 'admin']: #Админ в проекте не реализован
            return False, "Invalid role", None

        try:
            # Проверка на тавтологию username/email
            existing_user = db.execute_query(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email)
            )

            if existing_user:
                return False, "Username or email already exists", None

            hashed_password = AuthManager.hash_password(password)


            user_id = db.execute_insert(
                """
                INSERT INTO users (username, email, password_hash, first_name, last_name, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (username, email, hashed_password, first_name, last_name, role,
                 datetime.datetime.now().isoformat())
            )


            db.execute_insert(
                """
                INSERT INTO user_settings (user_id, created_at)
                VALUES (?, ?)
                """,
                (user_id, datetime.datetime.now().isoformat())
            )

            return True, "User  registered successfully", user_id
        except Exception as e:
            return False, f"Registration failed: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def login_user(username_or_email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Авторизация юзера
        Возвращаем кортеж (success, message, user_data).
        """
        db = get_db()

        try:
            is_email = '@' in username_or_email

            query = "SELECT id, username, email, password_hash, role, first_name, last_name FROM users WHERE "
            query += "email = ?" if is_email else "username = ?"
            query += " AND is_active = 1"

            users = db.execute_query(query, (username_or_email,))

            if not users:
                return False, "Invalid credentials", None

            user = dict(users[0])

            if not AuthManager.verify_password(password, user['password_hash']):
                return False, "Invalid credentials", None

            db.execute_update(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.datetime.now().isoformat(), user['id'])
            )

            token = AuthManager.generate_token(user['id'], user['role'])

            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'token': token
            }

            return True, "Login successful", user_data
        except Exception as e:
            return False, f"Login failed: {str(e)}", None
        finally:
            db.close()

    @staticmethod
    def check_permission(user_role: str, required_roles: list) -> bool:
        """Проверка роли на разрешение"""
        return user_role in required_roles

    @staticmethod
    def log_action(user_id: int, action: str, entity_type: str,
                   entity_id: Optional[int] = None, details: Optional[str] = None,
                   ip_address: Optional[str] = None) -> bool:
        """Логгирование"""
        db = get_db()

        try:
            db.execute_insert(
                """
                INSERT INTO audit_log (user_id, action, entity_type, entity_id, details, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, action, entity_type, entity_id, details, ip_address)
            )
            return True
        except Exception as e:
            print(f"Error logging action: {e}")
            return False
        finally:
            db.close()
