from unittest.mock import patch

import pytest

from app.services.config import (
    ActionBuilderConfig,
    get_api_key_config,
    get_recipient_emails,
)


# ----- get_recipient_emails tests -----
@patch("os.getenv", return_value="user1@example.com,user2@example.com")
def test_get_recipient_emails_multiple(mock_getenv):
    emails = get_recipient_emails()
    assert emails == ["user1@example.com", "user2@example.com"]


@patch("os.getenv", return_value="user1@example.com ,  user2@example.com , ")
def test_get_recipient_emails_with_spaces(mock_getenv):
    emails = get_recipient_emails()
    assert emails == ["user1@example.com", "user2@example.com"]


@patch("os.getenv", return_value="")
def test_get_recipient_emails_empty(mock_getenv):
    emails = get_recipient_emails()
    assert emails == []


# ----- get_api_key_config tests -----
@patch("os.getenv")
def test_get_api_key_config_success(mock_getenv):
    mock_getenv.side_effect = lambda key, default=None: {
        "API_KEY": "fake-api-key",
        "DOMAIN": "example.com",
        "CAMPAIGN_ID": "12345",
        "RECIPIENT_EMAILS": "user@example.com",
    }.get(key, default)

    config_obj = get_api_key_config()
    assert isinstance(config_obj, ActionBuilderConfig)
    assert config_obj.api_key == "fake-api-key"
    assert config_obj.domain == "example.com"
    assert config_obj.campaign_id == "12345"
    assert config_obj.recipient_emails == ["user@example.com"]


@patch("os.getenv", return_value=None)
def test_get_api_key_config_missing_key(mock_getenv):
    with pytest.raises(ValueError, match="API_KEY not found"):
        get_api_key_config()
