from typing import Any, Dict, Generator, List

import requests

from app.services.config import CONFIG
from app.services.utils import retry_request

BASE_URL = f"https://{CONFIG.domain}.actionbuilder.org/api/rest/v1/campaigns"
HEADERS = {"OSDI-API-Token": CONFIG.api_key, "Content-Type": "application/json"}

@retry_request()
def _fetch_campaigns_page(page: int, per_page: int) -> Dict[str, Any]:
    """Fetch a single page of campaigns."""
    params = {"page": page, "per_page": per_page}
    r = requests.get(BASE_URL, headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()


def get_campaigns_paginated(
    per_page: int = 25,
) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields campaigns with pagination.
    """
    page = 1
    while True:
        try:
            data = _fetch_campaigns_page(page, per_page)
        except requests.RequestException as e:
            print(f"Error fetching page {page}: {e}")
            break

        campaigns = data.get("_embedded", {}).get("action_builder:campaigns", [])
        if not campaigns:
            break

        yield from campaigns

        total_pages = data.get("total_pages")
        if total_pages is None or page >= total_pages:
            break

        page += 1


def get_all_campaigns(per_page: int = 25) -> List[Dict[str, Any]]:
    """Fetch all campaigns and return as a list."""
    return list(get_campaigns_paginated(per_page))


def get_campaigns() -> Dict[str, Any]:
    """
    Original function for backward compatibility.
    Returns only the first page of results.
    """
    r = requests.get(BASE_URL, headers=HEADERS)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    print("Fetching all campaigns with pagination:")
    for campaign in get_campaigns_paginated(per_page=50):
        print(f"ID: {campaign['identifiers']}, Name: {campaign['name']}")
