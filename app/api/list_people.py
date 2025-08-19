from typing import Any, Dict, Generator, List, Optional

import requests

from app.services.config import CONFIG
from app.services.utils import retry_request

BASE_URL = f"https://{CONFIG.domain}.actionbuilder.org/api/rest/v1/campaigns/{CONFIG.campaign_id}/people"
HEADERS = {
    "OSDI-API-Token": CONFIG.api_key,
    "Content-Type": "application/json",
}

@retry_request()
def _fetch_people_page(
    page: int,
    per_page: int,
    modified_before: Optional[str] = None,
    modified_after: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """Fetch a single page of people matching the modified_date filters."""
    filters = []
    if modified_before:
        filters.append(f"modified_date lt '{modified_before}'")
    if modified_after:
        filters.append(f"modified_date gt '{modified_after}'")

    params = {
        "page": page,
        "per_page": per_page,
    }
    if filters:
        params["filter"] = " and ".join(filters)

    if debug:
        print(f"Requesting: {BASE_URL} with {params}")

    r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)

    if debug and r.status_code != 200:
        print(f"Status: {r.status_code}, Body: {r.text[:500]}")

    r.raise_for_status()
    return r.json()


def search_people_modified_by(
    modified_before: Optional[str] = None,
    modified_after: Optional[str] = None,
    per_page: int = 25,
    debug: bool = False,
) -> Generator[Dict[str, Any], None, None]:
    """Yield people in the campaign modified before/after the given dates."""
    page = 1
    while True:
        try:
            data = _fetch_people_page(
                page, per_page, modified_before, modified_after, debug
            )
        except requests.RequestException as e:
            if debug:
                print(f"Request error: {e}")
            break
        except Exception as e:
            if debug:
                print(f"Unexpected error: {e}")
            break

        people = data.get("_embedded", {}).get("osdi:people", [])
        if not people:
            break

        yield from people

        total_pages = data.get("total_pages")
        if total_pages is None or page >= total_pages:
            break

        page += 1


def list_people_modified_by(
    modified_before: Optional[str] = None,
    modified_after: Optional[str] = None,
    per_page: int = 25,
) -> List[Dict[str, Any]]:
    """Return all people modified before/after given dates as a list."""
    return list(
        search_people_modified_by(
            modified_before=modified_before,
            modified_after=modified_after,
            per_page=per_page,
        )
    )


def search_all_people(
    per_page: int = 25, debug: bool = False
) -> Generator[Dict[str, Any], None, None]:
    """
    Yield all people in the campaign, with no date filters.
    Efficiently handles pagination using existing architecture.
    """
    page = 1
    while True:
        try:
            data = _fetch_people_page(page, per_page, debug=debug)
        except requests.RequestException as e:
            if debug:
                print(f"Request error: {e}")
            break
        except Exception as e:
            if debug:
                print(f"Unexpected error: {e}")
            break

        people = data.get("_embedded", {}).get("osdi:people", [])
        if not people:
            break

        yield from people

        total_pages = data.get("total_pages")
        if total_pages is None or page >= total_pages:
            break

        page += 1


def list_all_people(per_page: int = 25) -> List[Dict[str, Any]]:
    """Return all people in the campaign as a list."""
    return list(search_all_people(per_page=per_page))


if __name__ == "__main__":
    people = list_people_modified_by(modified_after="2025-08-09T00:00:00Z")
    print(f"Fetched {len(people)} people")
