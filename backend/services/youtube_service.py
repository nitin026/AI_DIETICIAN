"""
services/youtube_service.py
Fetches relevant YouTube recipe tutorial URLs for a given meal name.
Uses youtube-search-python (no API key required).
"""
from __future__ import annotations

from loguru import logger

try:
    from youtubesearchpython import VideosSearch
    YT_AVAILABLE = True
except ImportError:
    YT_AVAILABLE = False
    logger.warning("youtube-search-python not installed; YouTube links will be skipped.")


async def get_recipe_url(meal_name: str, cuisine: str = "Indian") -> str | None:
    """
    Return the first YouTube video URL for '{meal_name} {cuisine} recipe'.
    Returns None if unavailable.
    """
    if not YT_AVAILABLE:
        return None
    try:
        query = f"{meal_name} {cuisine} recipe"
        search = VideosSearch(query, limit=1)
        results = search.result()
        videos = results.get("result", [])
        if videos:
            url = videos[0].get("link")
            logger.debug("YouTube: '{}' → {}", query, url)
            return url
    except Exception as exc:
        logger.warning("YouTube search failed for '{}': {}", meal_name, exc)
    return None
