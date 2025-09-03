from typing import Any, Dict, List, Optional

import requests

from app.services.config import CONFIG
from app.services.utils import retry_request

HEADERS = {"OSDI-API-Token": CONFIG.api_key, "Content-Type": "application/json"}


@retry_request()
def _safe_get(url: str) -> Optional[Dict[str, Any]]:
    """Helper to GET JSON with consistent error handling."""
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_person(person_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a person resource from Action Builder API."""
    url = (
        f"https://{CONFIG.domain}.actionbuilder.org/api/rest/v1/"
        f"campaigns/{CONFIG.campaign_id}/people/{person_id}"
    )
    try:
        return _safe_get(url)
    except requests.RequestException as e:
        return None


def fetch_connections_from_person(person: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch all connection records for a given person, handling pagination.
    Returns an empty list if none are found.
    """
    url = person.get("_links", {}).get("action_builder:connections", {}).get("href")
    if not url:
        return []

    all_connections: List[Dict[str, Any]] = []

    while url:
        try:
            data = _safe_get(url)
        except requests.RequestException as e:
            data = None
        if not data:
            break

        # collect connections from this page
        connections = data.get("_embedded", {}).get("action_builder:connections", [])
        all_connections.extend(connections)

        # follow pagination
        url = data.get("_links", {}).get("next", {}).get("href")

    return all_connections


def fetch_connection_status_from_connections(
    connections: List[Dict[str, Any]],
) -> Optional[bool]:
    """Return True if the connection is active, false if inactive, None if not there"""
    for conn in connections:
        if conn.get("connection_type") == "People + Units":
            if conn.get("inactive"):
                return False
            else:
                return True
    return None


def fetch_unit_from_connection(
    connections: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Fetch the unit data for a connection of type 'People + Units'."""
    for conn in connections:
        if conn.get("connection_type") == "People + Units":
            if conn.get("inactive"):
                continue
            unit_url = conn.get("_links", {}).get("osdi:person", {}).get("href")
            if unit_url:
                try:
                    return _safe_get(unit_url)
                except requests.RequestException as e:
                    return None
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
            try:
                data = _safe_get(url)
            except requests.RequestException as e:
                data = None
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
    person_id = "145ca7d1-bc29-4cd6-a5cb-3dbbb9414815"

    person_data = get_person(person_id)
    if not person_data:
        print("Failed to retrieve person data.")
        exit(1)

    print("Person data retrieved successfully!")
    # print(person_data)

    connections_data = fetch_connections_from_person(person_data)
    # print(connections_data)

    status = fetch_connection_status_from_connections(connections_data)
    print(status)

    unit_data = fetch_unit_from_connection(connections_data)
    if unit_data:
        print(unit_data)
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
