import os
from dataclasses import dataclass

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


@dataclass
class ActionBuilderConfig:
    """
    A dataclass to hold configuration for API keys.
    Dataclasses are great for creating classes that primarily store data.
    """

    api_key: str
    domain: str
    campaign_id: str
    recipient_emails: list[str]
    smtp_username: str
    smtp_server: str
    smtp_port: int
    smtp_password: str


def get_recipient_emails():
    """
    Read the RECIPIENT_EMAILS environment variable and return as a list of strings.

    Returns:
        list: List of email addresses as strings
    """
    emails_str = os.getenv("RECIPIENT_EMAILS", "")

    if not emails_str:
        return []

    # Split by comma and strip whitespace from each email
    emails = [email.strip() for email in emails_str.split(",")]

    # Filter out any empty strings
    emails = [email for email in emails if email]

    return emails


def get_api_key_config() -> ActionBuilderConfig:
    """
    Loads the API key from the environment and returns an APIKeyConfig object.

    The function first checks if the API_KEY environment variable is set.
    It raises a ValueError if the key is not found, ensuring that the
    application won't proceed with a critical missing piece of information.
    """
    api_key_value = os.getenv("API_KEY")
    domain = os.getenv("DOMAIN")
    campaign_id = os.getenv("CAMPAIGN_ID")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_password = os.environ.get("SMTP_PASSWORD")
    if not api_key_value:
        raise ValueError(
            "API_KEY not found in environment variables. Please check your .env file."
        )

    return ActionBuilderConfig(
        api_key=api_key_value,
        domain=domain,
        campaign_id=campaign_id,
        recipient_emails=get_recipient_emails(),
        smtp_username=smtp_username,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        smtp_password=smtp_password,
    )


CONFIG = get_api_key_config()

if __name__ == "__main__":
    try:
        config = get_api_key_config()
        print("Successfully loaded API Key Configuration!")
        print(f"API Key: {config.api_key}")

    except ValueError as e:
        print(f"Error: {e}")
