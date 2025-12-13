import json
from urllib.parse import urlparse, quote_plus

import requests

from .. import LOGGER
from .utils.xtra import _sync_to_async

_BYPASS_CMD_TO_SERVICE = {
    "gdflix": "gdflix",
    "gdf": "gdflix",
    "extraflix": "extraflix",
    "hubcloud": "hubcloud",
    "hc": "hubcloud",
    "hubdrive": "hubdrive",
    "hd": "hubdrive",
    "hubcdn": "hubcdn",
    "hcdn": "hubcdn",
    "transfer_it": "transfer_it",
    "ti": "transfer_it",
    "vcloud": "vcloud",
    "vc": "vcloud",
    "driveleech": "driveleech",
    "dleech": "driveleech",
    "neo": "neo",
    "neolinks": "neo",
    "gdrex": "gdrex",
    "gdex": "gdrex",
    "pixelcdn": "pixelcdn",
    "pcdn": "pixelcdn",
    "extralink": "extralink",
    "luxdrive": "luxdrive",
    "nexdrive": "nexdrive",
    "nd": "nexdrive",
}

_BYPASS_ENDPOINTS = {
    # By : Hgbots
    "gdflix": "https://hgbots.vercel.app/bypaas/gd.php?url=",
    "hubdrive": "https://hgbots.vercel.app/bypaas/hubdrive.php?url=",  
   # By : NickUpdates 
    "transfer_it": "https://transfer-it-henna.vercel.app/post",
    # By: PBX1 
    "hubcloud": "https://pbx1botapi.vercel.app/api/hubcloud?url=",
    "vcloud": "https://pbx1botapi.vercel.app/api/vcloud?url=",
    "hubcdn": "https://pbx1botapi.vercel.app/api/hubcdn?url=",
    "driveleech": "https://pbx1botapi.vercel.app/api/driveleech?url=",
    "neo": "https://pbx1botapi.vercel.app/api/neo?url=",
    "gdrex": "https://pbx1botapi.vercel.app/api/gdrex?url=",
    "pixelcdn": "https://pbx1botapi.vercel.app/api/pixelcdn?url=",
    "extraflix": "https://pbx1botapi.vercel.app/api/extraflix?url=",
    "extralink": "https://pbx1botapi.vercel.app/api/extralink?url=",
    "luxdrive": "https://pbx1botapi.vercel.app/api/luxdrive?url=",
    "nexdrive": "https://pbx1botsapi2.vercel.app/api/nexdrive?url=",
}

def _bp_srv(cmd):
    cmd = cmd.lower().lstrip("/")
    return _BYPASS_CMD_TO_SERVICE.get(cmd)


def _bp_label_from_key(key):
    mapping = {
        "instant_final": "Instant",
        "cloud_r2": "Cloud R2",
        "zip_final": "ZIP",
        "pixeldrain": "Pixeldrain",
        "telegram_file": "Telegram",
        "gofile_final": "Gofile",
    }
    if key in mapping:
        return mapping[key]
    return key.replace("_", " ").title()


def _bp_label_from_name(name):
    s = str(name).strip()
    low = s.lower()
    if "[" in s and "]" in s and "download" in low:
        i1 = s.find("[")
        i2 = s.rfind("]")
        if i1 != -1 and i2 != -1 and i2 > i1:
            inner = s[i1 + 1 : i2].strip()
            if inner:
                return inner
    if low.startswith("download "):
        return s[8:].strip() or s
    return s


def _bp_links(links):
    if not isinstance(links, dict) or not links:
        return "• No direct links found."
    lines = []
    for label, url in links.items():
        if not isinstance(url, str):
            continue
        u = url.strip()
        if not u.startswith(("http://", "https://")):
            continue
        lbl = str(label).strip()
        if not lbl:
            lbl = "Link"
        lines.append(f"• <b>{lbl}:</b> <a href=\"{u}\">Click Here</a>")
    if not lines:
        return "• No direct links found."
    return "\n".join(lines)

def _bp_norm(data, service):
    root = data
    if isinstance(data, dict) and isinstance(data.get("final"), dict):
        root = data["final"]

    title = root.get("title") or data.get("title") or root.get("file_name") or data.get("file_name") or "N/A"
    filesize = root.get("filesize") or data.get("filesize") or root.get("file_size") or data.get("file_size") or "N/A"
    file_format = (
        root.get("format")
        or root.get("file_format")
        or data.get("format")
        or data.get("file_format")
        or "N/A"
    )

    links_clean = {}
    raw_links = None
    if isinstance(root, dict) and "links" in root:
        raw_links = root.get("links")
    elif isinstance(data, dict) and "links" in data:
        raw_links = data.get("links")
    if not raw_links and isinstance(data, dict) and "results" in data:
        results = data.get("results")
        if isinstance(results, list):
            for item in results:
                if not isinstance(item, dict):
                    continue
                lbl = item.get("quality") or item.get("name") or "Link"
                url = item.get("link") or item.get("url")
                if isinstance(url, str):
                    u = url.strip()
                    if u.startswith(("http://", "https://")):
                        links_clean[str(lbl).strip()] = u
            return {
                "title": str(data.get("title") or title or "N/A"),
                "filesize": str(data.get("filesize") or filesize or "N/A"),
                "format": str(data.get("format") or file_format or "N/A"),
                "links": links_clean,
                "service": service,
            }
    if isinstance(raw_links, list):
        for item in raw_links:
            if not isinstance(item, dict):
                continue
            lbl = item.get("type") or item.get("name") or "Link"
            url = item.get("url") or item.get("link")
            if not isinstance(url, str):
                continue
            u = url.strip()
            if not u.startswith(("http://", "https://")):
                continue
            links_clean[str(lbl).strip()] = u
    elif isinstance(raw_links, dict):
        for k, v in raw_links.items():
            if not isinstance(v, str) and not isinstance(v, dict):
                continue
            url = None
            lbl = _bp_label_from_key(k)
            if isinstance(v, str):
                url = v.strip()
            elif isinstance(v, dict):
                url = (
                    v.get("link")
                    or v.get("url")
                    or v.get("google_final")
                    or v.get("edited")
                    or v.get("telegram_file")
                    or v.get("gofile_final")
                )
                if v.get("name"):
                    lbl = _bp_label_from_name(v["name"])
            if not url:
                continue
            if not isinstance(url, str):
                continue
            u = url.strip()
            if not u.startswith(("http://", "https://")):
                continue
            links_clean[lbl] = u
    if not links_clean:
        skip = {"title", "filesize", "format", "file_format", "success", "links", "file_name", "file_size"}
        if isinstance(root, dict):
            for k, v in root.items():
                if k in skip:
                    continue
                url = None
                lbl = str(k)
                if isinstance(v, dict):
                    url = (
                        v.get("link")
                        or v.get("url")
                        or v.get("google_final")
                        or v.get("edited")
                        or v.get("telegram_file")
                        or v.get("gofile_final")
                    )
                    if v.get("name"):
                        lbl = _bp_label_from_name(v["name"])
                elif isinstance(v, str) and v.startswith(("http://", "https://")):
                    url = v
                    lbl = _bp_label_from_key(k)
                if not url:
                    continue
                if not isinstance(url, str):
                    continue
                u = url.strip()
                if not u.startswith(("http://", "https://")):
                    continue
                links_clean[lbl] = u

    return {
        "title": str(title),
        "filesize": str(filesize),
        "format": str(file_format),
        "links": links_clean,
        "service": service,
    }
    
async def _bp_info(cmd_name, target_url):
    service = _bp_srv(cmd_name)
    if not service:
        return None, "Unknown platform for this command."
    base = _BYPASS_ENDPOINTS.get(service)
    if not base:
        return None, "Bypass endpoint not configured for this service."
    try:
        parsed = urlparse(target_url)
        if not parsed.scheme or not parsed.netloc:
            return None, "Invalid URL."
    except Exception:
        return None, "Invalid URL."
    if service == "transfer_it":
        api_url = base
    else:
        api_url = f"{base}{quote_plus(target_url)}"
    LOGGER.info(f"Bypassing via [{service}] -> {api_url}")
    try:
        if service == "transfer_it":
            resp = await _sync_to_async(
                requests.post, api_url, json={"url": target_url}, timeout=20
            )
        else:
            resp = await _sync_to_async(requests.get, api_url, timeout=20)
    except Exception as e:
        LOGGER.error(f"Bypass HTTP error: {e}", exc_info=True)
        return None, "Failed to reach bypass service."
    if resp.status_code != 200:
        LOGGER.error(f"Bypass API returned {resp.status_code}: {resp.text[:200]}")
        return None, "Bypass service error."
    try:
        data = resp.json()
    except json.JSONDecodeError as e:
        LOGGER.error(f"Bypass JSON parse error: {e}")
        return None, "Invalid response from bypass service."
    if not isinstance(data, dict):
        return None, "Unexpected response from bypass service."
    if service == "transfer_it":
        direct = data.get("url")
        if not direct:
            return None, "File Expired or File Not Found"
        fake = {
            "title": "N/A",
            "filesize": "N/A",
            "format": "N/A",
            "links": {"Direct Link": str(direct)},
        }
        norm = _bp_norm(fake, service)
        return norm, None
    if "success" in data and not data.get("success"):
        return None, data.get("message") or "Bypass failed."
    norm = _bp_norm(data, service)
    return norm, None 
