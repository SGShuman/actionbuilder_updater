from typing import Any, Dict, Generator, List, Optional

import requests

from app.services.config import CONFIG
from app.services.utils import retry_request

BASE_URL = f"https://{CONFIG.domain}.actionbuilder.org/api/rest/v1/campaigns/{CONFIG.campaign_id}/people"
HEADERS = {
    "OSDI-API-Token": CONFIG.api_key,
    "Content-Type": "application/json",
}


def _build_filter_string(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    given_name: Optional[str] = None,
    family_name: Optional[str] = None,
    postal_code: Optional[str] = None,
    identifier: Optional[str] = None,
    custom_filters: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Create the Action Builder filter string from provided arguments."""
    filters = []
    if email:
        filters.append(f"email_address eq '{email}'")
    if phone:
        filters.append(f"phone_number eq '{phone}'")
    if given_name:
        filters.append(f"given_name eq '{given_name}'")
    if family_name:
        filters.append(f"family_name eq '{family_name}'")
    if postal_code:
        filters.append(f"postal_code eq '{postal_code}'")
    if identifier:
        filters.append(f"identifiers eq '{identifier}'")

    filter_string = " and ".join(filters) if filters else None

    # Merge custom filter string if provided
    if custom_filters and "filter" in custom_filters:
        custom_str = custom_filters["filter"]
        if filter_string:
            filter_string = f"({filter_string}) and ({custom_str})"
        else:
            filter_string = custom_str

    return filter_string

@retry_request()
def _fetch_people_page(
    page: int,
    per_page: int,
    filter_string: Optional[str] = None,
    custom_filters: Optional[Dict[str, Any]] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """Fetch one page of people with optional filters."""
    params = {"page": page, "per_page": per_page}
    if filter_string:
        params["filter"] = filter_string

    # Pass along other non-filter custom params
    if custom_filters:
        for key, value in custom_filters.items():
            if key != "filter":
                params[key] = str(value)

    if debug:
        print(f"Requesting: {BASE_URL} with params={params}")

    r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)

    if debug and r.status_code != 200:
        print(f"Status: {r.status_code}, Body: {r.text[:500]}")

    r.raise_for_status()
    return r.json()


def search_people_paginated(
    email: Optional[str] = None,
    phone: Optional[str] = None,
    given_name: Optional[str] = None,
    family_name: Optional[str] = None,
    postal_code: Optional[str] = None,
    identifier: Optional[str] = None,
    custom_filters: Optional[Dict[str, Any]] = None,
    per_page: int = 25,
    debug: bool = False,
) -> Generator[Dict[str, Any], None, None]:
    """Generator to search people in a campaign with pagination."""
    filter_string = _build_filter_string(
        email, phone, given_name, family_name, postal_code, identifier, custom_filters
    )

    page = 1
    while True:
        try:
            data = _fetch_people_page(page, per_page, filter_string, custom_filters, debug)
        except requests.RequestException as e:
            if debug:
                print(f"Request error on page {page}: {e}")
            break
        except Exception as e:
            if debug:
                print(f"Unexpected error on page {page}: {e}")
            break

        people = data.get("_embedded", {}).get("osdi:people", [])
        if not people:
            break

        yield from people

        total_pages = data.get("total_pages")
        if total_pages is None or page >= total_pages:
            break

        page += 1


# Convenience wrappers
def search_all_people(**kwargs) -> List[Dict[str, Any]]:
    """Return all people matching criteria as a list."""
    return list(search_people_paginated(**kwargs))


def search_people_by_email(email: str, **kwargs) -> Generator[Dict[str, Any], None, None]:
    yield from search_people_paginated(email=email, **kwargs)


def search_people_by_name(
    given_name: Optional[str] = None,
    family_name: Optional[str] = None,
    **kwargs
) -> Generator[Dict[str, Any], None, None]:
    yield from search_people_paginated(given_name=given_name, family_name=family_name, **kwargs)


def search_people_by_location(postal_code: str, **kwargs) -> Generator[Dict[str, Any], None, None]:
    yield from search_people_paginated(postal_code=postal_code, **kwargs)


def get_all_people_in_campaign(**kwargs) -> Generator[Dict[str, Any], None, None]:
    yield from search_people_paginated(**kwargs)


if __name__ == "__main__":
    print("Testing paginated email search:")
    for person in search_people_by_email("joelashuman@gmail.com", debug=True):
        print(person)
        print(f"Found: {person.get('given_name')} {person.get('family_name')}")
        emails = person.get("email_addresses", [])
        if emails:
            print(f"  Email: {emails[0].get('address')}")
        break
