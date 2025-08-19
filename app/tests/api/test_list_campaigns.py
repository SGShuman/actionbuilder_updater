from unittest.mock import Mock, patch

from requests.exceptions import ConnectionError, HTTPError

from app.api import list_campaigns

# Sample campaign data
SAMPLE_CAMPAIGN_PAGE = {
    "_embedded": {
        "action_builder:campaigns": [
            {"identifiers": ["abc-123"], "name": "Campaign 1"},
            {"identifiers": ["def-456"], "name": "Campaign 2"},
        ]
    },
    "total_pages": 2,
}

SAMPLE_EMPTY_PAGE = {
    "_embedded": {"action_builder:campaigns": []},
    "total_pages": 1,
}


def mock_requests_get(url, headers=None, params=None):
    """Return sample data based on page number"""
    page = params.get("page") if params else 1
    mock_response = Mock()
    if page == 1:
        mock_response.json.return_value = SAMPLE_CAMPAIGN_PAGE
    else:
        mock_response.json.return_value = SAMPLE_EMPTY_PAGE
    mock_response.raise_for_status.return_value = None
    return mock_response


@patch("app.api.list_campaigns.requests.get", side_effect=mock_requests_get)
def test_fetch_campaigns_page(mock_get):
    result = list_campaigns._fetch_campaigns_page(1, 25)
    assert result["_embedded"]["action_builder:campaigns"][0]["name"] == "Campaign 1"
    mock_get.assert_called_once()


@patch("app.api.list_campaigns.requests.get", side_effect=mock_requests_get)
def test_get_campaigns_paginated(mock_get):
    campaigns = list(list_campaigns.get_campaigns_paginated(per_page=2))
    assert len(campaigns) == 2
    assert campaigns[0]["name"] == "Campaign 1"


@patch("app.api.list_campaigns.requests.get", side_effect=mock_requests_get)
def test_get_all_campaigns(mock_get):
    campaigns = list_campaigns.get_all_campaigns(per_page=2)
    assert isinstance(campaigns, list)
    assert campaigns[0]["identifiers"] == ["abc-123"]


@patch("app.api.list_campaigns.requests.get")
def test_get_campaigns_first_page(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = SAMPLE_CAMPAIGN_PAGE
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    result = list_campaigns.get_campaigns()
    assert "_embedded" in result
    assert len(result["_embedded"]["action_builder:campaigns"]) == 2


# ----- ERROR HANDLING TESTS -----
@patch("app.api.list_campaigns.requests.get", side_effect=HTTPError("Server error"))
def test_get_campaigns_paginated_http_error(mock_get):
    campaigns = list(list_campaigns.get_campaigns_paginated(per_page=2))
    # Generator should exit gracefully on error
    assert campaigns == []


@patch(
    "app.api.list_campaigns.requests.get", side_effect=ConnectionError("Network error")
)
def test_get_campaigns_paginated_connection_error(mock_get):
    campaigns = list(list_campaigns.get_campaigns_paginated(per_page=2))
    assert campaigns == []
