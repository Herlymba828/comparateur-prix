import os
import time
from typing import Any, Dict, List, Optional

import requests


class EbayClient:
    """
    Minimal eBay Browse API client with application OAuth token (client credentials).
    Docs: https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
    """

    def __init__(self,
                 client_id: Optional[str] = None,
                 client_secret: Optional[str] = None,
                 env: Optional[str] = None,
                 timeout: int = 10):
        self.client_id = client_id or os.getenv("EBAY_CLIENT_ID") or os.getenv("EBAY_APP_ID")
        self.client_secret = client_secret or os.getenv("EBAY_CLIENT_SECRET")
        self.env = (env or os.getenv("EBAY_ENV", "production")).lower()
        self.timeout = timeout

        if self.env not in ("production", "sandbox"):
            self.env = "production"

        self._token: Optional[str] = None
        self._token_exp: float = 0.0

        self.identity_base = (
            "https://api.ebay.com" if self.env == "production" else "https://api.sandbox.ebay.com"
        )
        self.browse_base = (
            "https://api.ebay.com/buy/browse/v1"
            if self.env == "production" else
            "https://api.sandbox.ebay.com/buy/browse/v1"
        )

    def _ensure_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_exp - 30:
            return self._token
        if not (self.client_id and self.client_secret):
            raise RuntimeError("EBAY_CLIENT_ID/EBAY_CLIENT_SECRET are not configured")

        url = f"{self.identity_base}/identity/v1/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            # Minimum scope for Browse API public search
            "scope": "https://api.ebay.com/oauth/api_scope",
        }
        auth = (self.client_id, self.client_secret)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(url, data=data, auth=auth, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        js = resp.json()
        access_token = js.get("access_token")
        expires_in = int(js.get("expires_in", 7200))
        if not access_token:
            raise RuntimeError("Failed to obtain eBay access token")
        self._token = access_token
        self._token_exp = now + expires_in
        return access_token

    def search(self, q: str, limit: int = 10, offset: int = 0, marketplace: str = "EBAY_FR") -> Dict[str, Any]:
        """
        Search item summaries.
        marketplace: e.g., EBAY_FR, EBAY_US, EBAY_GB
        """
        token = self._ensure_token()
        params = {
            "q": q,
            "limit": max(1, min(int(limit), 50)),
            "offset": max(0, int(offset)),
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": marketplace,
        }
        url = f"{self.browse_base}/item_summary/search"
        resp = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def extract_items(search_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        return search_json.get("itemSummaries", [])
