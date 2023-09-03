from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.common.ldap import LDAPException
from app.config import Config

INSERT_SQL = '''
    INSERT INTO "users"
        ("login", "bind_token", "email2", "phone", "telegram", "otp", "reset_token", "bind_dest")
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
'''
UPDATE_SQL = '''
    UPDATE "users"
    SET "login" = ?,
        "bind_token" = ?,
        "email2" = ?,
        "phone" = ?,
        "telegram" = ?,
        "otp" = ?,
        "reset_token" = ?,
        "bind_dest" = ?
    WHERE "id" = ?
'''
FETCH_BY_LOGIN_SQL = '''
    SELECT "id", "bind_token", "email2", "phone", "telegram", "otp", "reset_token", "bind_dest"
    FROM "users"
    WHERE "login" = ?
'''
FETCH_BY_TELEGRAM_SQL = '''
    SELECT "login"
    FROM "users"
    WHERE "telegram" = ?
'''

logger = logging.getLogger(__name__)


class UserBindDestination(Enum):
    NONE = 0
    EMAIL = 1
    PHONE = 2
    TELEGRAM = 3
    OTP = 4


@dataclass
class User:
    id: Optional[int] = None
    login: Optional[str] = None
    bind_token: Optional[str] = None
    email2: Optional[str] = None
    phone: Optional[int] = None
    telegram: Optional[int] = None
    otp: Optional[str] = None
    reset_token: Optional[int] = None
    bind_dest: Optional[UserBindDestination] = None

    # only from LDAP
    name: Optional[str] = None

    def save(self):
        with Config.database.get_connection() as db:
            if self.id is None:
                cursor = db.execute(INSERT_SQL, (self.login, self.bind_token, self.email2,
                                    self.phone, self.telegram, self.otp, self.reset_token, self.bind_dest.value))
                self.id = cursor.lastrowid
                logger.info("User with login %s created", self.login)
            else:
                db.execute(UPDATE_SQL, (self.login, self.bind_token, self.email2, self.phone,
                                        self.telegram, self.otp, self.reset_token, self.bind_dest.value, self.id))
                logger.info("User with login %s updated", self.login)

    @staticmethod
    def find(login: str) -> User:
        ldap_user = Config.ldap_descriptor.get_user(login)
        cursor = Config.database.execute(FETCH_BY_LOGIN_SQL, (ldap_user.user_principal_name,))
        data = cursor.fetchone()
        if data is None:
            return User(login=ldap_user.user_principal_name, name=ldap_user.display_name)

        user = User(login=ldap_user.user_principal_name, name=ldap_user.display_name, id=data[0],
                    bind_token=data[1], email2=data[2], phone=data[3], telegram=data[4],
                    otp=data[5], reset_token=data[6], bind_dest=UserBindDestination(data[7]))
        logger.info("User found: %s", user)
        return user

    @staticmethod
    def try_find(login: str) -> Optional[User]:
        try:
            return User.find(login)
        except LDAPException as exception:
            logger.error("User.find(%s) failed: %s", login, exception)
            return None

    @staticmethod
    def try_find_by_telegram(tg_id: int) -> Optional[User]:
        cursor = Config.database.execute(FETCH_BY_TELEGRAM_SQL, (tg_id,))
        data = cursor.fetchone()
        if data is None:
            logger.info("User not found by Telegram ID: %d", tg_id)
            return None

        user = User.find(data[0])
        logger.info("User found by Telegram ID: %s", user.name)
        return user
