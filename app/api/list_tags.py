from typing import Any, Dict, Generator, List

import requests

from app.services.config import CONFIG
from app.services.utils import retry_request

BASE_URL = f"https://{CONFIG.domain}.actionbuilder.org/api/rest/v1/campaigns/{CONFIG.campaign_id}/people/"
HEADERS = {"OSDI-API-Token": CONFIG.api_key, "Content-Type": "application/json"}

@retry_request()
def _fetch_tag_page(person_id: str, page: int, per_page: int) -> Dict[str, Any]:
    """Fetch a single page of taggings for a person."""
    url = f"{BASE_URL}{person_id}/taggings"
    params = {"page": page, "per_page": per_page}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    return r.json()


def get_tags_paginated(
    person_id: str, per_page: int = 25
) -> Generator[Dict[str, Any], None, None]:
    """
    Generator that yields taggings for a person with pagination.
    """
    page = 1
    while True:
        try:
            data = _fetch_tag_page(person_id, page, per_page)
        except requests.RequestException as e:
            print(f"Error fetching page {page} for person {person_id}: {e}")
            break

        taggings = data.get("_embedded", {}).get("osdi:taggings", [])
        if not taggings:
            break

        yield from taggings

        total_pages = data.get("total_pages")
        if total_pages is None or page >= total_pages:
            break

        page += 1


def get_all_tags(person_id: str, per_page: int = 25) -> List[Dict[str, Any]]:
    """Fetch all taggings for a person and return as a list."""
    return list(get_tags_paginated(person_id, per_page))


if __name__ == "__main__":
    person_id = "7edd9555-3ff9-4833-9f3f-fdf4a064e8ec"  # replace with the person you want to fetch taggings for
    print(f"Fetching all taggings for person {person_id}:")
    # tags = _fetch_tag_page(person_id, page=1, per_page=50)
    # print(tags)
    for tagging in get_tags_paginated(person_id, per_page=50):
        print(
            f"ID: {tagging['identifiers']}, Field: {tagging.get('action_builder:field')}, Name: {tagging.get('action_builder:name')}"
        )
