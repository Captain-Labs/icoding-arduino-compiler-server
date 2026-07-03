# auth_db.py
# Hostinger MySQL database manager for premium user accounts and JWT sessions.
# Handles: user registration, login, token validation, plan upgrades, logout.

import os
import datetime
import secrets
import pymysql
import pymysql.cursors
import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

# ─── Config from environment ───────────────────────────────────────────────────
_DB_HOST         = os.getenv('DB_HOST', 'localhost')
_DB_PORT         = int(os.getenv('DB_PORT', 3306))
_DB_NAME         = os.getenv('DB_NAME', 'icoding_users')
_DB_USER         = os.getenv('DB_USER', 'root')
_DB_PASS         = os.getenv('DB_PASS', '')
_JWT_SECRET      = os.getenv('JWT_SECRET', 'changeme')
_JWT_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', 72))

# ─── DB Connection ─────────────────────────────────────────────────────────────
def _db_connect() -> pymysql.Connection:
    """Opens and returns a new MySQL connection using env credentials."""
    return pymysql.connect(
        host=_DB_HOST,
        port=_DB_PORT,
        user=_DB_USER,
        password=_DB_PASS,
        database=_DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=10
    )

# ─── Table Initialisation ──────────────────────────────────────────────────────
def init_db():
    """
    Creates the users and sessions tables if they don't already exist.
    Called once on server startup.
    """
    try:
        conn = _db_connect()
        with conn.cursor() as cur:
            # Users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id         INT AUTO_INCREMENT PRIMARY KEY,
                    email      VARCHAR(255) UNIQUE NOT NULL,
                    pw_hash    VARCHAR(255) NOT NULL,
                    plan       ENUM('free', 'premium') DEFAULT 'free',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            # Sessions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id         INT AUTO_INCREMENT PRIMARY KEY,
                    user_id    INT NOT NULL,
                    token      TEXT NOT NULL,
                    expires_at DATETIME NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
        conn.close()
        print("[Auth] MySQL tables initialised successfully.")
    except Exception as e:
        print(f"[Auth] WARNING: Could not initialise MySQL tables: {e}")
        print("[Auth] Premium auth endpoints will be unavailable until DB is configured.")

# ─── User Registration ─────────────────────────────────────────────────────────
def register_user(email: str, password: str) -> dict:
    """
    Registers a new user with plan=free.
    Returns {'success': True, 'user_id': id} or {'success': False, 'error': '...'}.
    """
    email = email.strip().lower()
    if not email or not password:
        return {'success': False, 'error': 'Email and password are required.'}
    if len(password) < 6:
        return {'success': False, 'error': 'Password must be at least 6 characters.'}
    if len(email) > 255 or '@' not in email:
        return {'success': False, 'error': 'Invalid email address.'}

    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        conn = _db_connect()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (email, pw_hash) VALUES (%s, %s)",
                (email, pw_hash)
            )
            user_id = cur.lastrowid
        conn.close()
        return {'success': True, 'user_id': user_id}
    except pymysql.err.IntegrityError:
        return {'success': False, 'error': 'An account with this email already exists.'}
    except Exception as e:
        return {'success': False, 'error': f'Database error: {str(e)}'}

# ─── User Login ────────────────────────────────────────────────────────────────
def login_user(email: str, password: str) -> dict:
    """
    Validates credentials, creates a session, and returns a signed JWT.
    Returns {'success': True, 'token': '...', 'user': {...}} or {'success': False, 'error': '...'}.
    """
    email = email.strip().lower()
    try:
        conn = _db_connect()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cur.fetchone()

        if not user:
            conn.close()
            return {'success': False, 'error': 'Invalid email or password.'}

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['pw_hash'].encode('utf-8')):
            conn.close()
            return {'success': False, 'error': 'Invalid email or password.'}

        # Create JWT
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=_JWT_EXPIRY_HOURS)
        payload = {
            'user_id': user['id'],
            'email': user['email'],
            'plan': user['plan'],
            'exp': expires_at
        }
        token = jwt.encode(payload, _JWT_SECRET, algorithm='HS256')

        # Store session in DB
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user['id'], token, expires_at.strftime('%Y-%m-%d %H:%M:%S'))
            )
        conn.close()

        return {
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'plan': user['plan']
            }
        }
    except Exception as e:
        return {'success': False, 'error': f'Login error: {str(e)}'}

# ─── Token Validation ──────────────────────────────────────────────────────────
def validate_token(token: str) -> dict | None:
    """
    Verifies the JWT signature, checks expiry, and confirms session exists in DB.
    Returns the decoded payload dict {'user_id', 'email', 'plan'} or None if invalid.
    """
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=['HS256'])

        # Also check session exists in DB (handles logout invalidation)
        conn = _db_connect()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM sessions WHERE token = %s AND expires_at > NOW()",
                (token,)
            )
            session = cur.fetchone()
        conn.close()

        if not session:
            return None  # Logged out or expired
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

# ─── Get User Info ─────────────────────────────────────────────────────────────
def get_user(user_id: int) -> dict | None:
    """Returns user row {id, email, plan, created_at} or None if not found."""
    try:
        conn = _db_connect()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, plan, created_at FROM users WHERE id = %s",
                (user_id,)
            )
            user = cur.fetchone()
        conn.close()
        return user
    except Exception:
        return None

# ─── Plan Upgrade ──────────────────────────────────────────────────────────────
def upgrade_to_premium(email: str) -> dict:
    """
    Sets a user's plan to 'premium'. Called by the /admin/upgrade endpoint
    after manual payment confirmation.
    """
    email = email.strip().lower()
    try:
        conn = _db_connect()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET plan = 'premium' WHERE email = %s",
                (email,)
            )
            affected = cur.rowcount
        conn.close()
        if affected == 0:
            return {'success': False, 'error': f'No user found with email: {email}'}
        return {'success': True, 'message': f'{email} upgraded to premium.'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ─── Downgrade to Free ─────────────────────────────────────────────────────────
def downgrade_to_free(email: str) -> dict:
    """Sets a user's plan back to 'free'."""
    email = email.strip().lower()
    try:
        conn = _db_connect()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET plan = 'free' WHERE email = %s",
                (email,)
            )
            affected = cur.rowcount
        conn.close()
        if affected == 0:
            return {'success': False, 'error': f'No user found with email: {email}'}
        return {'success': True, 'message': f'{email} downgraded to free.'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ─── Logout ───────────────────────────────────────────────────────────────────
def logout_user(token: str) -> dict:
    """
    Deletes the session row so the token is immediately invalidated.
    Even if the JWT hasn't expired, it won't pass validate_token() anymore.
    """
    try:
        conn = _db_connect()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE token = %s", (token,))
        conn.close()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

# ─── List All Users (Admin) ────────────────────────────────────────────────────
def list_users() -> list:
    """Returns all users (id, email, plan, created_at). For admin use only."""
    try:
        conn = _db_connect()
        with conn.cursor() as cur:
            cur.execute("SELECT id, email, plan, created_at FROM users ORDER BY created_at DESC")
            users = cur.fetchall()
        conn.close()
        # Convert datetime objects to strings for JSON serialisation
        for u in users:
            if u.get('created_at'):
                u['created_at'] = str(u['created_at'])
        return users
    except Exception:
        return []
