import logging
import re
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time


def get_logger(name: str = "scripts", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def _with_timeout(request_func, timeout: int):
    def wrapper(method, url, **kwargs):
        kwargs.setdefault("timeout", timeout)
        return request_func(method, url, **kwargs)

    return wrapper


def get_session(timeout: int = 20, retries: int = 3, backoff: float = 0.5) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=(500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
            "Accept-Language": "fr-FR,fr;q=0.9",
        }
    )
    session.request = _with_timeout(session.request, timeout)
    return session


def formater_prix_xaf(prix_str: str) -> Optional[float]:
    """Parse un prix XAF depuis une chaîne ("1 200 F", "1200 XAF")."""
    if not prix_str:
        return None
    s = prix_str.strip()
    s = re.sub(r"(?i)(xaf|fcfa|f\s*cfa|f)\b", "", s)
    s = s.replace("\xa0", " ")
    s = s.replace(" ", "")
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None


def safe_get(session: requests.Session, url: str, *, timeout: int | None = None, headers: dict | None = None, retries: int = 2, backoff_base: float = 0.5, backoff_factor: float = 2.0) -> Optional[requests.Response]:
    """GET avec backoff exponentiel additionnel pour 429 et 5xx."""
    logger = get_logger()
    delay = max(0.0, float(backoff_base))
    last_exc: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            resp = session.get(url, timeout=timeout, headers=headers)
            if resp.status_code in (429, 500, 502, 503, 504):
                logger.warning(f"HTTP {resp.status_code} {url} tentative {attempt+1}/{retries}")
                time.sleep(delay)
                delay *= backoff_factor
                continue
            return resp
        except requests.RequestException as exc:  # type: ignore
            last_exc = exc
            logger.warning(f"{exc.__class__.__name__} sur {url} tentative {attempt+1}/{retries}")
            time.sleep(delay)
            delay *= backoff_factor
    if last_exc:
        logger.error(f"Echec GET {url}: {last_exc}")
    return None


def normaliser_nom_produit(nom: str) -> str:
    if not nom:
        return ""
    nom = re.sub(r"\s+", " ", nom.strip())
    return nom[:200].title()


def nettoyer_marque(marque: Optional[str]) -> str:
    if not marque:
        return ""
    return re.sub(r"\s+", " ", marque.strip()).upper()[:100]