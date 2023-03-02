from __future__ import annotations
from dataclasses import dataclass
import logging
from typing import Optional

from app.config import Config

INSERT_SQL = '''
    INSERT INTO "users"
        ("login", "bind_token", "email2", "phone", "telegram", "otp", "reset_token")
    VALUES (?, ?, ?, ?, ?, ?, ?)
'''
UPDATE_SQL = '''
    UPDATE "users"
    SET "login" = ?,
        "bind_token" = ?,
        "email2" = ?,
        "phone" = ?,
        "telegram" = ?,
        "otp" = ?,
        "reset_token" = ?
    WHERE "id" = ?
'''
FETCH_SQL = 'SELECT "id", "login", "bind_token", "email2", "phone", "telegram", "otp", "reset_token" FROM "users"'
FETCH_BY_LOGIN_SQL = '''
    SELECT "id", "bind_token", "email2", "phone", "telegram", "otp", "reset_token"
    FROM "users"
    WHERE "login" = ?
'''
FETCH_BY_TELEGRAM_SQL = '''
    SELECT "login"
    FROM "users"
    WHERE "telegram" = ?
'''

logger = logging.getLogger(__name__)


@dataclass
class User:
    id: Optional[int] = None
    login: Optional[str] = None
    bind_token: Optional[str] = None
    email2: Optional[str] = None
    phone: Optional[int] = None
    telegram: Optional[int] = None
    otp: Optional[int] = None
    reset_token: Optional[int] = None

    # only from LDAP
    name: Optional[str] = None

    def save(self):
        with Config.database.get_connection() as db:
            if self.id is None:
                cursor = db.execute(INSERT_SQL, (self.login, self.bind_token, self.email2,
                                    self.phone, self.telegram, self.otp, self.reset_token))
                self.id = cursor.lastrowid
                logger.info(f"User with login {self.login} created")
            else:
                db.execute(UPDATE_SQL, (self.login, self.bind_token, self.email2,   self.phone,
                                        self.telegram, self.otp, self.reset_token, self.id))
                logger.info(f"User with login {self.login} updated")

    @staticmethod
    def find(login: str) -> User:
        ldap_user = Config.ldap_descriptor.getuser(login)
        if ldap_user is None:
            logger.warning(f"User with login {login} not found")
            return None

        upn, name, _ = ldap_user

        cursor = Config.database.execute(FETCH_BY_LOGIN_SQL, (upn,))
        data = cursor.fetchone()
        if data is None:
            return User(login=upn, name=name)

        user = User(login=upn, name=name, id=data[0],
                    bind_token=data[1], email2=data[2], phone=data[3],
                    telegram=data[4], otp=data[5], reset_token=data[6])
        logger.info(f"User found: {user}")
        return user

    @staticmethod
    def find_by_telegram(tg_id: int) -> User:
        cursor = Config.database.execute(FETCH_BY_TELEGRAM_SQL, (tg_id,))
        data = cursor.fetchone()
        if data is None:
            logger.info(f"User not found by Telegram ID: {tg_id}")
            return None

        user = User.find(data[0])
        logger.info(f"User found by Telegram ID: {user.name}")
        return user
