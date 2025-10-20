import os
import time
import logging
import re
from typing import Optional, Dict, Any

import requests
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


def _get_google_api_key() -> str:
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY manquant dans l'environnement")
    return api_key


def geocode_address(address: str, *, region_hint: str = "ga", retries: int = 3, backoff_sec: float = 0.8) -> Optional[Dict[str, Any]]:
    """Géocode une adresse via Google Geocoding API.
    Retourne un dict {lat, lng, formatted_address, place_id} ou None si échec.
    """
    if not address or not address.strip():
        return None

    # Cache lookup (sanitize key for memcached-compatible backends)
    raw_key = f"ggl:geocode:{region_hint}:{address.strip().lower()}"
    key = re.sub(r"[^a-z0-9:_-]+", "_", raw_key)
    key = key[:200]
    cached = cache.get(key)
    if cached is not None:
        return cached

    api_key = _get_google_api_key()
    endpoint = os.getenv("GOOGLE_GEOCODE_ENDPOINT", "https://maps.googleapis.com/maps/api/geocode/json")
    params_base = {
        "address": address,
        "key": api_key,
    }
    # Restreindre par pays si fourni (Google accepte param `region` en ccTLD/ISO2)
    region_hint = (region_hint or "").strip().lower()
    if region_hint:
        params_base["region"] = region_hint

    timeout = float(os.getenv("GOOGLE_TIMEOUT", "5"))
    last_exc = None
    for attempt in range(retries):
        try:
            resp = requests.get(endpoint, params=params_base, timeout=timeout)
            if resp.status_code == 200:
                payload = resp.json() or {}
                status = payload.get("status")
                results = payload.get("results", [])
                if status != "OK" or not results:
                    return None
                best = results[0]
                geom = (best.get("geometry") or {}).get("location") or {}
                data = {
                    "lat": float(geom.get("lat")) if geom.get("lat") is not None else None,
                    "lng": float(geom.get("lng")) if geom.get("lng") is not None else None,
                    "formatted_address": best.get("formatted_address", ""),
                    "place_id": best.get("place_id", ""),
                }
                if data["lat"] is None or data["lng"] is None:
                    return None
                ttl = int(os.getenv('GOOGLE_CACHE_TTL', '86400'))
                cache.set(key, data, ttl)
                return data
            elif 400 <= resp.status_code < 500:
                # Erreur côté client (ex: quota, clé invalide): ne pas réessayer inutilement
                logger.error("Google geocode 4xx (%s): %s", resp.status_code, resp.text[:200])
                return None
            else:
                # 5xx: backoff et retry
                sleep_s = backoff_sec * (2 ** attempt)
                logger.warning("Google geocode tentative %s échouée (HTTP %s). Retry in %.1fs", attempt + 1, resp.status_code, sleep_s)
                time.sleep(sleep_s)
        except requests.RequestException as exc:
            last_exc = exc
            sleep_s = backoff_sec * (2 ** attempt)
            logger.warning("Google geocode tentative %s échouée (%s). Retry in %.1fs", attempt + 1, exc, sleep_s)
            time.sleep(sleep_s)
    logger.error("Google geocode échec définitif pour '%s': %s", address, last_exc)
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
    # Nouvelles métadonnées si disponibles
    if hasattr(magasin, "formatted_address"):
        magasin.formatted_address = data.get("formatted_address", "")
    if hasattr(magasin, "place_id"):
        magasin.place_id = data.get("place_id", "")
    if hasattr(magasin, "geocoded_at"):
        magasin.geocoded_at = timezone.now()
    if hasattr(magasin, "geocoding_provider"):
        magasin.geocoding_provider = "Google"

    update_fields = [
        "latitude",
        "longitude",
    ]
    if hasattr(magasin, "formatted_address"):
        update_fields.append("formatted_address")
    if hasattr(magasin, "place_id"):
        update_fields.append("place_id")
    if hasattr(magasin, "geocoded_at"):
        update_fields.append("geocoded_at")
    if hasattr(magasin, "geocoding_provider"):
        update_fields.append("geocoding_provider")

    magasin.save(update_fields=update_fields)
    return True
