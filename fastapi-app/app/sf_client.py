import os
from typing import Any, Dict, Optional

from simple_salesforce import Salesforce, SalesforceAuthenticationFailed


class SalesforceClient:
    """
    Wrapper for Salesforce REST API using simple-salesforce.
    """

    def __init__(self) -> None:
        self._sf: Optional[Salesforce] = None
        self._connected = False

    def _connect(self) -> None:
        if self._connected:
            return

        username = os.getenv("SF_USERNAME")
        password = os.getenv("SF_PASSWORD")
        token = os.getenv("SF_TOKEN")
        domain = os.getenv("SF_DOMAIN", "login")

        if not all([username, password, token]):
            self._sf = None
            return

        try:
            self._sf = Salesforce(
                username=username,
                password=password,
                security_token=token,
                domain=domain,
            )
            self._connected = True
        except SalesforceAuthenticationFailed:
            self._sf = None
            raise

    def get_status(self) -> Dict[str, Any]:
        try:
            self._connect()

            if not self._sf:
                return {
                    "org": None,
                    "contacts_count": None,
                    "status": "disabled",
                }

            query_result = self._sf.query("SELECT count() FROM Contact")
            total = query_result.get("totalSize")

            return {
                "org": self._sf.sf_instance,
                "contacts_count": total,
                "status": "ok",
            }

        except SalesforceAuthenticationFailed:
            return {
                "org": None,
                "contacts_count": None,
                "status": "auth_error",
            }
        except Exception:
            return {
                "org": None,
                "contacts_count": None,
                "status": "error",
            }
