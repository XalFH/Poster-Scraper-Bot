import re
import json
from urllib.parse import urlparse, quote_plus
import requests
from .. import LOGGER
from .utils.xtra import _sync_to_async


def _collect_url_pairs(node, out_list, parent_key=""):
    if isinstance(node, dict):
        for k, v in node.items():
            key = f"{parent_key}.{k}" if parent_key else str(k)
            _collect_url_pairs(v, out_list, key)
    elif isinstance(node, (list, tuple)):
        for idx, v in enumerate(node):
            key = f"{parent_key}[{idx}]" if parent_key else str(idx)
            _collect_url_pairs(v, out_list, key)
    elif isinstance(node, str):
        v = node.strip()
        if v.startswith("http://") or v.startswith("https://"):
            out_list.append((parent_key.lower(), v))


def _looks_like_image(url: str) -> bool:
    url_l = url.lower()
    if any(url_l.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".avif", ".jfif")):
        return True
    if any(x in url_l for x in ["image", "img", "poster", "cover", "banner", "art", "thumb"]):
        return True
    return False


_CMD_TO_PROVIDER = {
    "prime": "primevideo", "pv": "primevideo",
    "zee5": "zee5", "z5": "zee5",
    "appletv": "appletv", "atv": "appletv",
    "airtel": "airtelxstream", "ax": "airtelxstream",
    "sunnxt": "sunnxt", "sn": "sunnxt",
    "aha": "ahavideo", "ah": "ahavideo",
    "iqiyi": "iqiyi", "iq": "iqiyi",
    "wetv": "wetv", "wt": "wetv",
    "shemaroo": "shemaroo", "sm": "shemaroo",
    "bms": "bookmyshow", "bm": "bookmyshow",
    "plex": "plextv", "px": "plextv",
    "adda": "addatimes", "ad": "addatimes",
    "stage": "stage", "stg": "stage",
    "netflix": "netflix", "nf": "netflix",
    "mxplayer": "mxplayer", "mx": "mxplayer",
    "youtube": "ytdl", "yt": "ytdl",
    "instagram": "instagram", "ig": "instagram",
    "facebook": "facebook", "fb": "facebook",
    "tiktok": "tiktok", "tk": "tiktok",
    "crunchyroll": "crunchyroll", "cr": "crunchyroll",
}

_PROVIDER_NAMES = {
    "primevideo": "Prime Video",
    "zee5": "ZEE5",
    "appletv": "Apple TV+",
    "airtelxstream": "Airtel Xstream",
    "sunnxt": "Sun NXT",
    "ahavideo": "Aha Video",
    "iqiyi": "iQIYI",
    "wetv": "WeTV",
    "shemaroo": "ShemarooMe",
    "bookmyshow": "BookMyShow",
    "plextv": "Plex TV",
    "addatimes": "Addatimes",
    "stage": "Stage",
    "netflix": "Netflix",
    "mxplayer": "MX Player",
    "ytdl": "YouTube",
    "instagram": "Instagram",
    "facebook": "Facebook",
    "tiktok": "TikTok",
    "crunchyroll": "Crunchyroll",
}

_WORKERS = {
   # "primevideo": "https://primevideo.the-zake.workers.dev/?url=", Under Maintenance 
    "zee5": "https://zee5.the-zake.workers.dev/?url=",
    "appletv": "https://appletv.the-zake.workers.dev/?url=",
    "airtelxstream": "https://airtelxstream.the-zake.workers.dev/?url=",
    "sunnxt": "https://sunnxt.the-zake.workers.dev/?url=",
    "ahavideo": "https://ahavideo.the-zake.workers.dev/?url=",
    "iqiyi": "https://iqiyi.the-zake.workers.dev/?url=",
    "wetv": "https://wetv.the-zake.workers.dev/?url=",
    "shemaroo": "https://shemaroo.the-zake.workers.dev/?url=",
    "bookmyshow": "https://bookmyshow.the-zake.workers.dev/?url=",
    "plextv": "https://plextv.the-zake.workers.dev/?url=",
    "addatimes": "https://addatimes.the-zake.workers.dev/?url=",
    "stage": "https://stage.the-zake.workers.dev/?url=",
    "netflix": "https://netflix.the-zake.workers.dev/?url=",
    "mxplayer": "https://mxplayer.the-zake.workers.dev/?url=",
    "ytdl": "https://youtubedl.the-zake.workers.dev/?url=",
    "instagram": "https://instagramdl.the-zake.workers.dev/?url=",
    "facebook": "https://facebookdl.the-zake.workers.dev/?url=",
    "tiktok": "https://tiktokdl.the-zake.workers.dev/?url=",
    "crunchyroll": "https://crunchyroll.blaze-updatez.workers.dev/?q=",
    "primevideo": "https://primevideo.pbx1bots.workers.dev/?url=",
}


def _extract_url_from_message(message):
    if getattr(message, "command", None) and len(message.command) > 1:
        return " ".join(message.command[1:]).strip()

    if message.reply_to_message:
        text = message.reply_to_message.text or message.reply_to_message.caption or ""
        return text.strip()

    return None


def _provider_from_cmd(cmd: str):
    return _CMD_TO_PROVIDER.get(cmd.lower().lstrip("/"))


def _normalize_ott_json(provider: str, data: dict):
    if provider == "crunchyroll":
        images = data.get("images", {}) or {}
        return {
            "title": data.get("title", "N/A"),
            "year": str(data.get("year", data.get("metadata", {}).get("release_year", "N/A"))),
            "type": "Anime Series",
            "poster": images.get("portrait_poster"),
            "landscape": images.get("landscape_poster") or images.get("banner_backdrop"),
            "raw": data,
            "source": "Crunchyroll",
        }

    root = data.get("data", data)

    poster = root.get("portrait") or root.get("poster") or root.get("poster_url") or root.get("thumbnail") or root.get("image") or root.get("image_url")
    landscape = root.get("landscape") or root.get("banner") or root.get("backdrop")

    urls = []
    _collect_url_pairs(data, urls)
    image_urls = [v for _, v in urls if _looks_like_image(v)]

    if not poster and image_urls:
        poster = image_urls[0]
    if not landscape and len(image_urls) > 1:
        landscape = image_urls[1]

    return {
        "title": str(root.get("title", "N/A")),
        "year": str(root.get("year", "N/A")),
        "type": str(root.get("type", "N/A")),
        "poster": poster,
        "landscape": landscape,
        "raw": data,
        "source": _PROVIDER_NAMES.get(provider, provider),
    }


async def _fetch_ott_info(cmd_name: str, target: str):
    provider = _provider_from_cmd(cmd_name)
    if not provider:
        return None, "Unknown platform."

    base = _WORKERS.get(provider)
    if not base:
        return None, "Worker not configured."

    if provider != "crunchyroll":
        try:
            parsed = urlparse(target)
            if not parsed.scheme or not parsed.netloc:
                return None, "Invalid URL."
        except Exception:
            return None, "Invalid URL."

    worker_url = f"{base}{quote_plus(target)}"
    LOGGER.info(f"Fetching OTT via {worker_url}")

    try:
        resp = await _sync_to_async(requests.get, worker_url, timeout=15)
    except Exception:
        return None, "Worker request failed."

    if resp.status_code != 200:
        return None, f"Worker error {resp.status_code}"

    try:
        data = resp.json()
    except Exception:
        return None, "Invalid JSON response."

    return _normalize_ott_json(provider, data), None
