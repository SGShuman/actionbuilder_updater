from unittest.mock import Mock, patch

import pytest

import app.api.list_people as list_people

FAKE_PERSON = {"id": "123", "given_name": "Test", "family_name": "User"}


# ----------------------
# _fetch_people_page tests
# ----------------------
@patch("app.api.list_people.requests.get")
def test_fetch_people_page_success(mock_get):
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "_embedded": {"osdi:people": [FAKE_PERSON]},
        "total_pages": 1,
    }
    mock_get.return_value = mock_resp

    result = list_people._fetch_people_page(page=1, per_page=10)
    assert "_embedded" in result
    assert result["_embedded"]["osdi:people"][0]["id"] == "123"
    mock_get.assert_called_once()


@patch("app.api.list_people.requests.get")
def test_fetch_people_page_http_error(mock_get):
    mock_resp = Mock()
    mock_resp.raise_for_status.side_effect = Exception("Boom")
    mock_get.return_value = mock_resp

    with pytest.raises(Exception):
        list_people._fetch_people_page(page=1, per_page=10)


# ----------------------
# search_people_modified_by tests
# ----------------------
@patch("app.api.list_people._fetch_people_page")
def test_search_people_modified_by(mock_fetch):
    mock_fetch.side_effect = [
        {"_embedded": {"osdi:people": [FAKE_PERSON]}, "total_pages": 2},
        {"_embedded": {"osdi:people": []}, "total_pages": 2},
    ]
    people = list(list_people.search_people_modified_by())
    assert people[0]["id"] == "123"
    assert len(people) == 1


# ----------------------
# list_people_modified_by tests
# ----------------------
@patch("app.api.list_people.search_people_modified_by")
def test_list_people_modified_by(mock_search):
    mock_search.return_value = [FAKE_PERSON]
    result = list_people.list_people_modified_by()
    assert result == [FAKE_PERSON]


# ----------------------
# search_all_people tests
# ----------------------
@patch("app.api.list_people._fetch_people_page")
def test_search_all_people(mock_fetch):
    mock_fetch.side_effect = [
        {"_embedded": {"osdi:people": [FAKE_PERSON]}, "total_pages": 1}
    ]
    people = list(list_people.search_all_people())
    assert people[0]["id"] == "123"


# ----------------------
# list_all_people tests
# ----------------------
@patch("app.api.list_people.search_all_people")
def test_list_all_people(mock_search):
    mock_search.return_value = [FAKE_PERSON]
    result = list_people.list_all_people()
    assert result == [FAKE_PERSON]
