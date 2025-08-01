# Steam Game Search - Simple AppID Search
import requests
from typing import List, Dict, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(name)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

def find_appid(game_name: str, cc: str = "us", lang: str = "en") -> int | None:
    """
    Search the Steam Store for a game by name and return its AppID.
    Falls back to the first result if an exact match isn't found.
    
    Args:
        game_name (str): Name of the game to search for
        cc (str): Country code (default: "us")
        lang (str): Language code (default: "en")
    
    Returns:
        int | None: AppID if found, None otherwise
    """
    logger.debug(f"Searching for game: '{game_name}' (cc={cc}, lang={lang})")
    
    url = "https://store.steampowered.com/api/storesearch"
    params = {
        "term": game_name,
        "cc": cc,
        "l": lang
    }
    
    try:
        logger.debug(f"Making request to Steam API: {url}")
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        items = data.get("items", [])
        logger.debug(f"Steam API returned {len(items)} results")

        # Try to find an exact (case‐insensitive) match first
        for item in items:
            if item.get("name", "").lower() == game_name.lower():
                app_id = item.get("id")
                logger.info(f"Found exact match for '{game_name}': AppID {app_id}")
                return app_id

        # Otherwise return the first result
        if items:
            app_id = items[0].get("id")
            first_result_name = items[0].get("name", "Unknown")
            logger.info(f"No exact match found, returning first result: '{first_result_name}' (AppID {app_id})")
            return app_id

        logger.warning(f"No results found for game: '{game_name}'")
        return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while searching for '{game_name}': {e}")
        logger.debug(f"Network error details:", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error searching for game '{game_name}': {e}")
        logger.debug(f"Search error details:", exc_info=True)
        return None

def search_games(game_name: str, max_results: int = 20, cc: str = "us", lang: str = "en") -> List[Dict[str, any]]:
    """
    Search for multiple games and return up to max_results.
    
    Args:
        game_name (str): Name of the game to search for
        max_results (int): Maximum number of results to return (default: 20)
        cc (str): Country code (default: "us")
        lang (str): Language code (default: "en")
    
    Returns:
        List[Dict]: List of game dictionaries with appid, name, and type
    """
    logger.debug(f"Searching for multiple games: '{game_name}' (max_results={max_results}, cc={cc}, lang={lang})")
    
    url = "https://store.steampowered.com/api/storesearch"
    params = {
        "term": game_name,
        "cc": cc,
        "l": lang
    }
    
    try:
        logger.debug(f"Making request to Steam API: {url}")
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        items = data.get("items", [])
        logger.debug(f"Steam API returned {len(items)} total results")
        
        # Limit results to max_results
        limited_items = items[:max_results]
        logger.debug(f"Limited to {len(limited_items)} results")
        
        # Format results for GUI use
        results = []
        for item in limited_items:
            game_data = {
                "appid": item.get("id"),
                "name": item.get("name", "Unknown"),
                "type": item.get("type", "game")
            }
            results.append(game_data)
            logger.debug(f"Added result: {game_data['name']} (AppID: {game_data['appid']})")
        
        logger.info(f"Found {len(results)} games for search term '{game_name}'")
        return results
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while searching for games '{game_name}': {e}")
        logger.debug(f"Network error details:", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Error searching for games '{game_name}': {e}")
        logger.debug(f"Search error details:", exc_info=True)
        return []

def get_game_info(appid: int) -> Optional[Dict[str, any]]:
    """
    Get detailed game information by AppID.
    
    Args:
        appid (int): Steam AppID
    
    Returns:
        Dict | None: Game information if found, None otherwise
    """
    logger.debug(f"Getting detailed game info for AppID: {appid}")
    
    url = "https://store.steampowered.com/api/appdetails"
    params = {
        "appids": str(appid),
        "l": "english"
    }
    
    try:
        logger.debug(f"Making request to Steam API: {url}")
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        app_data = data.get(str(appid))
        
        if app_data and app_data.get("success"):
            game_data = app_data.get("data", {})
            game_info = {
                "appid": appid,
                "name": game_data.get("name", "Unknown"),
                "type": game_data.get("type", "game"),
                "short_description": game_data.get("short_description", ""),
                "header_image": game_data.get("header_image", ""),
                "developers": game_data.get("developers", []),
                "publishers": game_data.get("publishers", []),
                "release_date": game_data.get("release_date", {}).get("date", "Unknown")
            }
            logger.info(f"Retrieved game info for '{game_info['name']}' (AppID: {appid})")
            return game_info
        
        logger.warning(f"No game data found for AppID: {appid}")
        return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while getting info for AppID {appid}: {e}")
        logger.debug(f"Network error details:", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Error getting game info for AppID {appid}: {e}")
        logger.debug(f"Game info error details:", exc_info=True)
        return None


def get_game_name_by_appid(appid: str) -> str:
    """
    Get the game name by AppID. Returns AppID as fallback if name not found.
    
    Args:
        appid (str): Steam AppID as string
    
    Returns:
        str: Game name if found, otherwise "AppID {appid}"
    """
    logger.debug(f"Getting game name for AppID: {appid}")
    
    try:
        game_info = get_game_info(int(appid))
        if game_info and game_info.get("name"):
            game_name = game_info["name"]
            logger.debug(f"Found game name for AppID {appid}: '{game_name}'")
            return game_name
        else:
            logger.warning(f"No game name found for AppID {appid}, using fallback")
            return f"AppID {appid}"
    except Exception as e:
        logger.error(f"Error getting game name for AppID {appid}: {e}")
        logger.debug(f"Game name error details:", exc_info=True)
        return f"AppID {appid}"



