from typing import Any, Dict, List, Optional

import requests

from app.services.config import CONFIG
from app.services.utils import retry_request

HEADERS = {"OSDI-API-Token": CONFIG.api_key, "Content-Type": "application/json"}


@retry_request(retry_if_false=True)
def _safe_get(url: str) -> Optional[Dict[str, Any]]:
    """Helper to GET JSON with consistent error handling."""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        print(f"HTTP error: {e} - {response.text}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    return None


def get_person(person_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a person resource from Action Builder API."""
    url = (
        f"https://{CONFIG.domain}.actionbuilder.org/api/rest/v1/"
        f"campaigns/{CONFIG.campaign_id}/people/{person_id}"
    )
    return _safe_get(url)


def fetch_connections_from_person(person: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch all connection records for a given person, handling pagination.
    Returns an empty list if none are found.
    """
    url = person.get("_links", {}).get("action_builder:connections", {}).get("href")
    if not url:
        return []

    all_connections: List[Dict[str, Any]] = []

    while url:
        data = _safe_get(url)
        if not data:
            break

        # collect connections from this page
        connections = data.get("_embedded", {}).get("action_builder:connections", [])
        all_connections.extend(connections)

        # follow pagination
        url = data.get("_links", {}).get("next", {}).get("href")

    return all_connections


def fetch_unit_from_connection(
    connections: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Fetch the unit data for a connection of type 'People + Units'."""
    for conn in connections:
        if conn.get("connection_type") == "People + Units":
            unit_url = conn.get("_links", {}).get("osdi:person", {}).get("href")
            if unit_url:
                return _safe_get(unit_url)
    return None


def fetch_taggings_from_connection(
    connections: List[Dict[str, Any]],
) -> Optional[List[Dict[str, Any]]]:
    """Fetch all taggings for a connection of type 'People + Units', handling pagination."""

    for conn in connections:
        if conn.get("connection_type") != "People + Units":
            continue

        taggings_url = conn.get("_links", {}).get("osdi:taggings", {}).get("href")
        if not taggings_url:
            continue

        all_taggings: List[Dict[str, Any]] = []
        url = taggings_url

        while url:
            data = _safe_get(url)
            if not data:
                break

            # collect taggings from this page
            taggings = data.get("_embedded", {}).get("osdi:taggings", [])
            all_taggings.extend(taggings)

            # move to next page if available
            url = data.get("_links", {}).get("next", {}).get("href")

        return all_taggings

    return None


if __name__ == "__main__":
    person_id = "7e4cf4b3-f88e-4b4d-9359-165be5ac5260"

    person_data = get_person(person_id)
    if not person_data:
        print("Failed to retrieve person data.")
        exit(1)

    print("Person data retrieved successfully!")
    # print(person_data)

    connections_data = fetch_connections_from_person(person_data)
    # print(connections_data)

    unit_data = fetch_unit_from_connection(connections_data)
    if unit_data:
        # print(unit_data)
        print(unit_data.get("action_builder:name"))
    else:
        print("No unit data found.")

    taggings_data = fetch_taggings_from_connection(connections_data)
    # print(taggings_data)
    if taggings_data:
        member_status = None
        member_type = None

        for t in taggings_data:
            field = t.get("action_builder:field")
            name = t.get("action_builder:name")
            if field == "Membership Status":
                member_status = name
            elif field == "Membership Type":
                member_type = name

        print("Member Status:", member_status)
        print("Member Type:", member_type)
    else:
        print("No taggings data found.")
