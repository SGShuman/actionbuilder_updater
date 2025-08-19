from app.services.config import CONFIG

import requests

if __name__ == '__main__':

    email = "joelashuman@gmail.com"
    url = f"https://{CONFIG.domain}.actionbuilder.org/api/rest/v1/campaigns/{CONFIG.campaign_id}/people?filter=email_address eq '{email}'"
    headers = {
        "OSDI-API-Token": CONFIG.api_key,
        "Content-Type": "application/json"
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    print(data)

    for person in data.get("_embedded", {}).get("osdi:people", []):
        print(person["identifiers"], person.get("given_name"), person.get("family_name"))
