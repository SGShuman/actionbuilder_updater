from typing import Dict, Optional

import requests

from app.services.config import CONFIG
from app.services.utils import retry_request

BASE_PERSON_URL = f"https://{CONFIG.domain}.actionbuilder.org/api/rest/v1/campaigns/{CONFIG.campaign_id}/people"
HEADERS = {"OSDI-API-Token": CONFIG.api_key, "Content-Type": "application/json"}

@retry_request()
def update_tagging(
    person_id: str,
    field_name: str,
    value: str,
    tagging_id: Optional[str] = None,
) -> Dict:
    """
    Generic function to update or create a tagging on a person.

    Args:
        person_id: UUID of the person.
        field_name: Name of the field (e.g., 'Membership Status').
        value: Value to set.
        tagging_id: If updating an existing tagging, its ID. Otherwise, creates a new tagging.

    Returns:
        Response JSON from the API.
    """
    payload = {
        "origin_system": "SyncScript",
        "action_builder:section": "Membership",
        "action_builder:field": field_name,
        "action_builder:field_type": "standard",
        "name": value,
    }

    if tagging_id:
        url = f"{BASE_PERSON_URL}/{person_id}/taggings/{tagging_id}"
        response = requests.post(url, json=payload, headers=HEADERS)
    else:
        url = f"{BASE_PERSON_URL}/{person_id}/taggings"
        response = requests.post(url, json=payload, headers=HEADERS)

    response.raise_for_status()
    return response.json()


def update_membership_taggings(
    person_id: str,
    membership_status: str,
    membership_type: str,
    existing_taggings: Dict[str, str] = None,
) -> None:
    """
    Update the two membership-related taggings on a person.

    Args:
        person_id: UUID of the person.
        membership_status: Value for Membership Status (e.g., 'Active').
        membership_type: Value for Membership Type (e.g., 'Member').
        existing_taggings: Optional dict of existing tagging IDs with keys:
            'Membership Status', 'Membership Type'
    """
    # Update Membership Status
    status_id = (
        existing_taggings.get("Membership Status") if existing_taggings else None
    )
    update_tagging(
        person_id, "Membership Status", membership_status, tagging_id=status_id
    )

    # Update Membership Type
    type_id = existing_taggings.get("Membership Type") if existing_taggings else None
    update_tagging(person_id, "Membership Type", membership_type, tagging_id=type_id)


if __name__ == "__main__":
    # Example usage
    person_uuid = "7edd9555-3ff9-4833-9f3f-fdf4a064e8ec"
    existing = {
        "Membership Status": "b124271b-192c-499b-9f8a-081509762b79",
        "Membership Type": "876f000c-8551-48af-9b73-8f1eb8899f13",
    }

    update_membership_taggings(
        person_uuid, "Active", "Member", existing_taggings=existing
    )
