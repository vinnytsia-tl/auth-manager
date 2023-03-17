import logging
from typing import Tuple

import ldap3

from .config import LDAPConfig

logger = logging.getLogger(__name__)


class LDAPException(Exception):
    pass


class LDAPBindException(LDAPException):
    pass


class LDAPSearchException(LDAPException):
    pass


class LDAP():
    config: LDAPConfig
    server: ldap3.Server

    def __init__(self, config: LDAPConfig):
        self.config = config
        self.server = ldap3.Server(
            config.ldap_server, config.ldap_port, use_ssl=config.ldap_use_ssl)

    def set_password(self, username, password) -> bool:
        conn = ldap3.Connection(self.server, user=self.config.admin_user,
                                password=self.config.admin_password, version=3)
        if not conn.bind():
            logger.error('LDAP bind failed with user %s',
                         self.config.admin_user)
            raise LDAPBindException(f"LDAP bind failed with user {self.config.admin_user}")

        _, _, distinguished_name = self.getuser(username)
        return conn.extend.microsoft.modify_password(distinguished_name, password)

    def getuser(self, user_principal_name, search_base=None) -> Tuple[str, str, str]:
        if search_base is None:
            search_base = self.config.user_base

        conn = ldap3.Connection(self.server, user=self.config.admin_user,
                                password=self.config.admin_password, read_only=True, version=3)
        if not conn.bind():
            logger.error('LDAP bind failed with user %s',
                         self.config.admin_user)
            raise LDAPBindException(f"LDAP bind failed with user {self.config.admin_user}")

        user_principal_name = self.normalize_login(user_principal_name)
        search_filter = f'(&(objectCategory=person)(objectClass=user)(userPrincipalName={user_principal_name}))'
        attrs = ['userPrincipalName', 'displayName', 'distinguishedName']
        if not conn.search(search_base, search_filter, attributes=attrs):
            logger.error(
                'No LDAP entries found for search base %s and filter %s', search_base, search_filter)
            raise LDAPSearchException(f"No LDAP entries found for search base {search_base} and filter {search_filter}")

        entry = conn.entries[0]
        if entry is not None:
            logger.info(
                'Found LDAP entry for search base %s and filter %s', search_base, search_filter)
            return (entry.userPrincipalName.value, entry.displayName.value, entry.distinguishedName.value)

        logger.warning('No LDAP entry found for user %s in search base %s',
                       user_principal_name, search_base)
        raise LDAPSearchException(f"No LDAP entry found for user {user_principal_name} in search base {search_base}")

    def login(self, username, password) -> bool:
        if username is None or username == '' or password is None or password == '':
            logger.warning(
                "LDAP login without username/password is unsupported")
            return False

        username = self.normalize_login(username)
        conn = ldap3.Connection(self.server, user=username, password=password)
        if not conn.bind():
            logger.warning("LDAP bind failed with user %s", username)
            return False

        return True

    def normalize_login(self, login):
        login_part = login.split('@')
        if len(login_part) == 1:
            return f"{login_part[0]}@{self.config.ldap_request_domain}"

        return login
