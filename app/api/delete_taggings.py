import requests

from app.services.config import CONFIG
from app.services.utils import retry_request

BASE_URL = f"https://{CONFIG.domain}.actionbuilder.org/api/rest/v1/campaigns/{CONFIG.campaign_id}/people/"
HEADERS = {"OSDI-API-Token": CONFIG.api_key, "Content-Type": "application/json"}


@retry_request()
def delete_tagging(person_id: str, tagging_id: str) -> bool:
    """
    Delete a tagging for a given person.

    Returns True if deletion was successful, False otherwise.
    """
    url = f"{BASE_URL}{person_id}/taggings/{tagging_id}"
    r = requests.delete(url, headers=HEADERS)
    
    if r.status_code in {200, 204}:
        return True
    elif r.status_code == 404:
        # Tagging not found — treat as "already deleted"
        return False
    else:
        # Let other HTTP errors trigger retry
        r.raise_for_status()


if __name__ == "__main__":
    person_id = "7edd9555-3ff9-4833-9f3f-fdf4a064e8ec"  # replace with actual person
    tagging_id = (
        "6f3136ca-8d68-4c84-b22c-93960ae6adac"  # replace with actual tagging id
    )
    success = delete_tagging(person_id, tagging_id)
    print("Deleted successfully!" if success else "Failed to delete tagging.")
