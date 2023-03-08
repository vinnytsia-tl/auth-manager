from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass
class LDAPConfig:
    ldap_server: str
    ldap_port: int
    ldap_use_ssl: bool
    ldap_request_domain: str
    admin_user: str
    admin_password: str
    user_base: str

    @staticmethod
    def from_env() -> LDAPConfig:
        return LDAPConfig(
            ldap_server=getenv("LDAP_SERVER"),
            ldap_port=int(getenv("LDAP_PORT")),
            ldap_use_ssl=bool(getenv("LDAP_USE_SSL")),
            ldap_request_domain=getenv("LDAP_REQUEST_DOMAIN"),
            admin_user=getenv("LDAP_ADMIN_USER"),
            admin_password=getenv("LDAP_ADMIN_PASSWORD"),
            user_base=getenv("LDAP_USER_BASE")
        )
