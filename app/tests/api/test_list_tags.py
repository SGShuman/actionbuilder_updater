from unittest.mock import Mock, patch

from requests.exceptions import ConnectionError, HTTPError

from app.api import list_tags

# Sample tag data
SAMPLE_TAG_PAGE = {
    "_embedded": {
        "osdi:taggings": [
            {
                "identifiers": ["tag-1"],
                "action_builder:name": "Tag 1",
                "action_builder:field": "status",
            },
            {
                "identifiers": ["tag-2"],
                "action_builder:name": "Tag 2",
                "action_builder:field": "type",
            },
        ]
    },
    "total_pages": 2,
}

SAMPLE_EMPTY_PAGE = {
    "_embedded": {"osdi:taggings": []},
    "total_pages": 1,
}


def mock_requests_get(url, headers=None, params=None):
    """Return sample data based on page number"""
    page = params.get("page") if params else 1
    mock_response = Mock()
    if page == 1:
        mock_response.json.return_value = SAMPLE_TAG_PAGE
    else:
        mock_response.json.return_value = SAMPLE_EMPTY_PAGE
    mock_response.raise_for_status.return_value = None
    return mock_response


@patch("app.api.list_tags.requests.get", side_effect=mock_requests_get)
def test_fetch_tag_page(mock_get):
    person_id = "person-123"
    result = list_tags._fetch_tag_page(person_id, page=1, per_page=25)
    assert result["_embedded"]["osdi:taggings"][0]["action_builder:name"] == "Tag 1"
    mock_get.assert_called_once()


@patch("app.api.list_tags.requests.get", side_effect=mock_requests_get)
def test_get_tags_paginated(mock_get):
    person_id = "person-123"
    taggings = list(list_tags.get_tags_paginated(person_id, per_page=2))
    assert len(taggings) == 2
    assert taggings[0]["identifiers"] == ["tag-1"]


@patch("app.api.list_tags.requests.get", side_effect=mock_requests_get)
def test_get_all_tags(mock_get):
    person_id = "person-123"
    taggings = list_tags.get_all_tags(person_id, per_page=2)
    assert isinstance(taggings, list)
    assert taggings[1]["action_builder:field"] == "type"


# ----- ERROR HANDLING TESTS -----
@patch("app.api.list_tags.requests.get", side_effect=HTTPError("Server error"))
def test_get_tags_paginated_http_error(mock_get):
    person_id = "person-123"
    taggings = list(list_tags.get_tags_paginated(person_id, per_page=2))
    # Generator should exit gracefully on HTTPError
    assert taggings == []


@patch("app.api.list_tags.requests.get", side_effect=ConnectionError("Network error"))
def test_get_tags_paginated_connection_error(mock_get):
    person_id = "person-123"
    taggings = list(list_tags.get_tags_paginated(person_id, per_page=2))
    # Generator should exit gracefully on ConnectionError
    assert taggings == []
