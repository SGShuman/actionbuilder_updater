from unittest.mock import Mock, patch

import pytest
import requests

import app.api.update_person_tagging as update_tagging_module

FAKE_PERSON_ID = "123"
FAKE_TAGGING_ID = "abc"
FAKE_RESPONSE = {"id": "tag123", "name": "Active"}


# ----------------------
# update_tagging tests
# ----------------------
@patch("app.api.update_person_tagging.requests.post")
def test_update_tagging_create(mock_post):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = FAKE_RESPONSE
    mock_post.return_value = mock_resp

    result = update_tagging_module.update_tagging(
        person_id=FAKE_PERSON_ID, field_name="Membership Status", value="Active"
    )

    assert result == FAKE_RESPONSE
    url_used = f"https://{update_tagging_module.CONFIG.domain}.actionbuilder.org/api/rest/v1/campaigns/{update_tagging_module.CONFIG.campaign_id}/people/{FAKE_PERSON_ID}/taggings"
    mock_post.assert_called_once_with(
        url_used,
        json=mock_post.call_args.kwargs["json"],
        headers=update_tagging_module.HEADERS,
    )


@patch("app.api.update_person_tagging.requests.post")
def test_update_tagging_update_existing(mock_post):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = FAKE_RESPONSE
    mock_post.return_value = mock_resp

    result = update_tagging_module.update_tagging(
        person_id=FAKE_PERSON_ID,
        field_name="Membership Type",
        value="Member",
        tagging_id=FAKE_TAGGING_ID,
    )

    assert result == FAKE_RESPONSE
    url_used = f"https://{update_tagging_module.CONFIG.domain}.actionbuilder.org/api/rest/v1/campaigns/{update_tagging_module.CONFIG.campaign_id}/people/{FAKE_PERSON_ID}/taggings/{FAKE_TAGGING_ID}"
    mock_post.assert_called_once_with(
        url_used,
        json=mock_post.call_args.kwargs["json"],
        headers=update_tagging_module.HEADERS,
    )


@patch("app.api.update_person_tagging.requests.post")
def test_update_tagging_http_error(mock_post):
    """Test that an HTTP error is propagated."""
    mock_resp = Mock()
    mock_resp.raise_for_status.side_effect = requests.HTTPError("API failure")
    mock_post.return_value = mock_resp

    with pytest.raises(requests.HTTPError):
        update_tagging_module.update_tagging(
            person_id=FAKE_PERSON_ID, field_name="Membership Status", value="Active"
        )


# ----------------------
# update_membership_taggings tests
# ----------------------
@patch("app.api.update_person_tagging.update_tagging")
def test_update_membership_taggings_calls_update_tagging(mock_update):
    existing = {"Membership Status": "status123", "Membership Type": "type123"}

    update_tagging_module.update_membership_taggings(
        FAKE_PERSON_ID,
        membership_status="Active",
        membership_type="Member",
        existing_taggings=existing,
    )

    assert mock_update.call_count == 2
    # Check first call is for Membership Status
    first_call_args = mock_update.call_args_list[0]
    assert first_call_args[0][1] == "Membership Status"  # field_name
    assert first_call_args[0][2] == "Active"            # value
    assert first_call_args[1]["tagging_id"] == "status123"

    # Check second call is for Membership Type
    second_call_args = mock_update.call_args_list[1]
    assert second_call_args[0][1] == "Membership Type"  # field_name
    assert second_call_args[0][2] == "Member"          # value
    assert second_call_args[1]["tagging_id"] == "type123"


@patch("app.api.update_person_tagging.update_tagging")
def test_update_membership_taggings_without_existing(mock_update):
    update_tagging_module.update_membership_taggings(
        FAKE_PERSON_ID,
        membership_status="Active",
        membership_type="Member",
        existing_taggings=None,
    )
    assert mock_update.call_count == 2
    for call_args in mock_update.call_args_list:
        assert call_args[1]["tagging_id"] is None
