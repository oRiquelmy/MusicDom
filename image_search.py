"""Image search helpers for MusicDom.

Provides a single function `fetch_image_url(query, min_size=...)` that tries
multiple search engines (Bing and Google image search) to collect candidate
image URLs and picks a high-quality candidate by validating image headers
(Content-Type + Content-Length) with lightweight HEAD requests.
"""
from __future__ import annotations

import json
import time
import requests
from bs4 import BeautifulSoup as bs
from typing import Iterable, Optional
from urllib.parse import urlparse, parse_qs, unquote

# Reasonable default headers to avoid immediate blocking
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def _candidates_from_bing(query: str) -> Iterable[str]:
    try:
        params = {"q": query}
        r = requests.get("https://www.bing.com/images/search", params=params, headers=HEADERS, timeout=8)
        soup = bs(r.content, "html.parser")
        # Bing stores metadata in a JSON 'm' attribute on <a class="iusc"> elements
        for a in soup.select("a.iusc"):
            m = a.get("m")
            if not m:
                continue
            try:
                data = json.loads(m)
                murl = data.get("murl")
                if murl:
                    yield murl
            except Exception:
                continue
        # Fallback: img tags
        for img in soup.select("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-iurl")
            if src and src.startswith("http"):
                yield src
    except Exception:
        return


def _candidates_from_google(query: str) -> Iterable[str]:
    try:
        params = {"q": query, "tbm": "isch"}
        r = requests.get("https://www.google.com/search", params=params, headers=HEADERS, timeout=8)
        soup = bs(r.content, "html.parser")
        # Try common attributes that may contain full-size image URLs
        for img in soup.select("img"):
            src = img.get("data-iurl") or img.get("data-src") or img.get("src") or img.get("data-url")
            if src and src.startswith("http"):
                yield src
        # Look for anchors that use imgres or imgurl query params
        for a in soup.select("a"):
            href = a.get("href", "")
            if "imgurl=" in href:
                try:
                    part = href.split("imgurl=", 1)[1]
                    url = unquote(part.split("&")[0])
                    if url.startswith("http"):
                        yield url
                except Exception:
                    continue
    except Exception:
        return


def _validate_image(url: str, min_size: int = 30 * 1024) -> Optional[int]:
    """Return content-length if URL is an image and >= min_size, else None.

    Performs a HEAD request to avoid downloading full image. If server doesn't
    return content-length, we treat it pessimistically but accept common image
    content-types.
    """
    try:
        head = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        ct = head.headers.get("content-type", "")
        if not ct.startswith("image"):
            return None
        cl = head.headers.get("content-length")
        if cl:
            try:
                length = int(cl)
                if length >= min_size:
                    return length
                return None
            except Exception:
                # Unknown content-length, accept this image but with unknown size
                return 1
        # No content-length header, accept as image but unknown size
        return 1
    except Exception:
        return None


def fetch_image_url(query: str, min_size: int = 30 * 1024, max_candidates: int = 40) -> Optional[str]:
    """Return a high-quality image URL for the given query or None.

    Strategy:
    - Query Bing first (often provides full-size URLs via JSON) then Google.
    - Validate candidates via HEAD; prefer first with content-length >= min_size.
    - If none meet min_size but some are images, choose the largest available.
    """
    if not query:
        return None

    seen = set()
    candidates = []

    # Collect candidates from multiple sources
    for fn in (_candidates_from_bing, _candidates_from_google):
        for url in fn(query):
            if len(candidates) >= max_candidates:
                break
            if not url or url in seen:
                continue
            seen.add(url)
            candidates.append(url)
        if len(candidates) >= max_candidates:
            break

    best_unknown = None
    best_size = 0

    for url in candidates:
        size = _validate_image(url, min_size=min_size)
        if size and size >= min_size:
            return url
        if size and size > best_size:
            best_unknown = url
            best_size = size

    # If none passed size threshold, return the largest/first acceptable image
    if best_unknown:
        return best_unknown

    # As a last resort, return the first http candidate
    return next((u for u in candidates if u.startswith("http")), None)