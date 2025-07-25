# Steam Game Search - Simple AppID Search
import requests
from typing import List, Dict, Optional

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
    url = "https://store.steampowered.com/api/storesearch"
    params = {
        "term": game_name,
        "cc": cc,
        "l": lang
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        items = data.get("items", [])

        # Try to find an exact (case‐insensitive) match first
        for item in items:
            if item.get("name", "").lower() == game_name.lower():
                return item.get("id")

        # Otherwise return the first result
        if items:
            return items[0].get("id")

        return None
    
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except Exception as e:
        print(f"Error searching for game: {e}")
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
    url = "https://store.steampowered.com/api/storesearch"
    params = {
        "term": game_name,
        "cc": cc,
        "l": lang
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        items = data.get("items", [])
        
        # Limit results to max_results
        limited_items = items[:max_results]
        
        # Format results for GUI use
        results = []
        for item in limited_items:
            results.append({
                "appid": item.get("id"),
                "name": item.get("name", "Unknown"),
                "type": item.get("type", "game")
            })
        
        return results
    
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
    except Exception as e:
        print(f"Error searching for games: {e}")
        return []

def get_game_info(appid: int) -> Optional[Dict[str, any]]:
    """
    Get detailed game information by AppID.
    
    Args:
        appid (int): Steam AppID
    
    Returns:
        Dict | None: Game information if found, None otherwise
    """
    url = "https://store.steampowered.com/api/appdetails"
    params = {
        "appids": str(appid),
        "l": "english"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        app_data = data.get(str(appid))
        
        if app_data and app_data.get("success"):
            game_data = app_data.get("data", {})
            return {
                "appid": appid,
                "name": game_data.get("name", "Unknown"),
                "type": game_data.get("type", "game"),
                "short_description": game_data.get("short_description", ""),
                "header_image": game_data.get("header_image", ""),
                "developers": game_data.get("developers", []),
                "publishers": game_data.get("publishers", []),
                "release_date": game_data.get("release_date", {}).get("date", "Unknown")
            }
        
        return None
    
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return None
    except Exception as e:
        print(f"Error getting game info: {e}")
        return None


if __name__ == "__main__":
    name = input("Enter the Steam game name: ").strip()
    appid = find_appid(name)
    if appid:
        print(f"Found AppID for \"{name}\": {appid}")
    else:
        print(f"No results for \"{name}\".")
