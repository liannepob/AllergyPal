import secrets
import hashlib
from datetime import datetime, timedelta

def generate_token(db, user_id):
    token = secrets.token_urlsafe(32)
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now()
    duration = timedelta(minutes=30)
    expire_time = now + duration


    db.execute("INSERT INTO password_resets(user_id, token_hash, expires_at, used_at) VALUES(?, ?, ?, ?)",
                user_id, hashed_token, expire_time, None
            )
    return token

def verify_token(db, token):
    hashed_token = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now()

    # needs to look up the hash in password_resets
    look_up = db.execute("""SELECT user_id, token_hash, expires_at, used_at
                            FROM password_resets
                            WHERE token_hash = ?""",
                            hashed_token)
    if not look_up:
        return None
    else: 
        row = look_up[0]

    hashed = row["token_hash"]
    expire = datetime.fromisoformat(row["expires_at"])
    used = row["used_at"]

    if expire < now:
        return "reset token expired"
    elif used is not None:
        return "reset token has already been used"
    else:
        return row["user_id"]

