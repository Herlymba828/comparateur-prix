import os
import time
import logging
from typing import Optional, Dict, Any

import requests
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_here_api_key() -> str:
    api_key = os.getenv("HERE_API_KEY", "")
    if not api_key:
        raise RuntimeError("HERE_API_KEY manquant dans l'environnement")
    return api_key


def geocode_address(address: str, *, region_hint: str = "ga", retries: int = 3, backoff_sec: float = 0.8) -> Optional[Dict[str, Any]]:
    """Géocode une adresse via HERE Geocoding & Search API.
    Retourne un dict {lat, lng, formatted_address, place_id} ou None si échec.
    """
    if not address or not address.strip():
        return None

    # Cache lookup
    key = f"here:geocode:{region_hint}:{address.strip().lower()}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    api_key = _get_here_api_key()
    endpoint = os.getenv("HERE_GEOCODE_ENDPOINT", "https://geocode.search.hereapi.com/v1/geocode")
    params_base = {
        "q": address,
        "apiKey": api_key,
    }
    # Restreindre par pays si fourni
    region_hint = (region_hint or "").strip().lower()
    if region_hint:
        # ISO2 attendu par HERE (ex: GA, FR)
        params_base["in"] = f"countryCode:{region_hint.upper()}"

    timeout = float(os.getenv("HERE_TIMEOUT", "5"))
    last_exc = None
    for attempt in range(retries):
        try:
            resp = requests.get(endpoint, params=params_base, timeout=timeout)
            if resp.status_code == 200:
                payload = resp.json() or {}
                items = payload.get("items", [])
                if not items:
                    return None
                best = items[0]
                pos = best.get("position", {})
                data = {
                    "lat": float(pos.get("lat")) if pos.get("lat") is not None else None,
                    "lng": float(pos.get("lng")) if pos.get("lng") is not None else None,
                    "formatted_address": best.get("address", {}).get("label", ""),
                    "place_id": best.get("id", ""),
                }
                if data["lat"] is None or data["lng"] is None:
                    return None
                ttl = int(os.getenv('HERE_CACHE_TTL', '86400'))
                cache.set(key, data, ttl)
                return data
            elif 400 <= resp.status_code < 500:
                # Erreur côté client (ex: quota, clé invalide): ne pas réessayer inutilement
                logger.error("HERE geocode 4xx (%s): %s", resp.status_code, resp.text[:200])
                return None
            else:
                # 5xx: backoff et retry
                sleep_s = backoff_sec * (2 ** attempt)
                logger.warning("HERE geocode tentative %s échouée (HTTP %s). Retry in %.1fs", attempt + 1, resp.status_code, sleep_s)
                time.sleep(sleep_s)
        except requests.RequestException as exc:
            last_exc = exc
            sleep_s = backoff_sec * (2 ** attempt)
            logger.warning("HERE geocode tentative %s échouée (%s). Retry in %.1fs", attempt + 1, exc, sleep_s)
            time.sleep(sleep_s)
    logger.error("HERE geocode échec définitif pour '%s': %s", address, last_exc)
    return None


def geocode_magasin(magasin) -> bool:
    """Géocode un objet Magasin (si lat/lon manquants) en construisant une adresse complète.
    Retourne True si une mise à jour a été effectuée, False sinon.
    """
    if getattr(magasin, "latitude", None) is not None and getattr(magasin, "longitude", None) is not None:
        return False

    parts = []
    if magasin.adresse:
        parts.append(magasin.adresse)
    if getattr(magasin, "ville", None):
        parts.append(getattr(magasin.ville, "nom", ""))
        if getattr(magasin.ville, "region", None):
            parts.append(getattr(magasin.ville.region, "nom", ""))
    # Pays par défaut
    parts.append(os.getenv("DEFAULT_COUNTRY_NAME", "Gabon"))

    full_addr = ", ".join([p for p in parts if p])
    data = geocode_address(full_addr)
    if not data:
        return False

    magasin.latitude = data["lat"]
    magasin.longitude = data["lng"]
    magasin.formatted_address = data.get("formatted_address", "")
    magasin.place_id = data.get("place_id", "")
    magasin.geocoded_at = timezone.now()
    magasin.geocoding_provider = "here"
    magasin.save(update_fields=[
        "latitude", "longitude", "formatted_address", "place_id", "geocoded_at", "geocoding_provider"
    ])
    return True
