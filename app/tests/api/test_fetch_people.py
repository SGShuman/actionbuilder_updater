from unittest.mock import MagicMock, patch

import pytest
import requests

# Import the module under test
from app.api.fetch_people import (
    HEADERS,
    _safe_get,
    fetch_connections_from_person,
    fetch_taggings_from_connection,
    fetch_unit_from_connection,
    get_person,
)

# Note: All tests use explicit mocking to prevent real HTTP calls


# Safety net to prevent any real HTTP requests
@pytest.fixture(autouse=True)
def prevent_real_requests(monkeypatch):
    """Auto-use fixture that prevents any real HTTP requests during tests."""

    def raise_on_request(*args, **kwargs):
        raise Exception(
            f"Real HTTP request attempted to {args[0] if args else 'unknown URL'}! All requests should be mocked."
        )

    # Block all HTTP methods at the requests module level
    monkeypatch.setattr("requests.get", raise_on_request)
    monkeypatch.setattr("requests.post", raise_on_request)
    monkeypatch.setattr("requests.put", raise_on_request)
    monkeypatch.setattr("requests.delete", raise_on_request)
    monkeypatch.setattr("requests.patch", raise_on_request)


@pytest.fixture
def sample_person_data():
    """Sample person data for testing."""
    return {
        "identifiers": ["action_builder:7edd9555-3ff9-4833-9f3f-fdf4a064e8ec"],
        "given_name": "John",
        "family_name": "Doe",
        "_links": {
            "action_builder:connections": {
                "href": "https://example.actionbuilder.org/api/rest/v1/people/123/connections"
            }
        },
    }


@pytest.fixture
def sample_connections_data():
    """Sample connections data for testing."""
    return {
        "_embedded": {
            "action_builder:connections": [
                {
                    "connection_type": "People + Units",
                    "_links": {
                        "osdi:person": {
                            "href": "https://example.actionbuilder.org/api/rest/v1/units/456"
                        },
                        "osdi:taggings": {
                            "href": "https://example.actionbuilder.org/api/rest/v1/people/123/taggings"
                        },
                    },
                },
                {
                    "connection_type": "Other Connection",
                    "_links": {
                        "osdi:person": {
                            "href": "https://example.actionbuilder.org/api/rest/v1/units/789"
                        }
                    },
                },
            ]
        }
    }


@pytest.fixture
def sample_unit_data():
    """Sample unit data for testing."""
    return {
        "identifiers": ["action_builder:unit-456"],
        "action_builder:name": "Local Union 123",
        "name": "Local Union 123",
    }


@pytest.fixture
def sample_taggings_data():
    """Sample taggings data for testing."""
    return {
        "_embedded": {
            "osdi:taggings": [
                {
                    "action_builder:field": "Membership Status",
                    "action_builder:name": "Active",
                },
                {
                    "action_builder:field": "Membership Type",
                    "action_builder:name": "Full Member",
                },
                {
                    "action_builder:field": "Other Field",
                    "action_builder:name": "Other Value",
                },
            ]
        }
    }


class TestSafeGet:
    """Tests for the _safe_get helper function."""

    @patch("app.api.fetch_people.requests.get")
    def test_safe_get_success(self, mock_get):
        """Test successful GET request."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = _safe_get("https://example.com/api/test")

        # Assert
        assert result == {"data": "test"}
        mock_get.assert_called_once_with(
            "https://example.com/api/test", headers=HEADERS
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("builtins.print")
    @patch("app.api.fetch_people.requests.get")
    def test_safe_get_http_error(self, mock_get, mock_print):
        """Test GET request with HTTP error."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Error")
        mock_get.return_value = mock_response

        # Act
        result = _safe_get("https://example.com/api/test")

        # Assert
        assert result is None

    @patch("builtins.print")
    @patch("app.api.fetch_people.requests.get")
    def test_safe_get_connection_error(self, mock_get, mock_print):
        """Test GET request with connection error."""
        # Arrange
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        # Act
        result = _safe_get("https://example.com/api/test")

        # Assert
        assert result is None

    @patch("builtins.print")
    @patch("app.api.fetch_people.requests.get")
    def test_safe_get_timeout_error(self, mock_get, mock_print):
        """Test GET request with timeout error."""
        # Arrange
        mock_get.side_effect = requests.Timeout("Request timed out")

        # Act
        result = _safe_get("https://example.com/api/test")

        # Assert
        assert result is None

    @patch("builtins.print")
    @patch("app.api.fetch_people.requests.get")
    def test_safe_get_generic_request_exception(self, mock_get, mock_print):
        """Test GET request with generic request exception."""
        # Arrange
        mock_get.side_effect = requests.RequestException("Generic error")

        # Act
        result = _safe_get("https://example.com/api/test")

        # Assert
        assert result is None


class TestGetPerson:
    """Tests for the get_person function."""

    @patch("app.api.fetch_people._safe_get")
    @patch("app.api.fetch_people.CONFIG")
    def test_get_person_success(self, mock_config, mock_safe_get, sample_person_data):
        """Test successful person retrieval."""
        # Arrange
        mock_config.domain = "test-domain"
        mock_config.campaign_id = "test-campaign-123"
        mock_safe_get.return_value = sample_person_data

        # Act
        result = get_person("person-123")

        # Assert
        assert result == sample_person_data
        expected_url = "https://test-domain.actionbuilder.org/api/rest/v1/campaigns/test-campaign-123/people/person-123"
        mock_safe_get.assert_called_once_with(expected_url)

    @patch("app.api.fetch_people._safe_get")
    @patch("app.api.fetch_people.CONFIG")
    def test_get_person_failure(self, mock_config, mock_safe_get):
        """Test person retrieval failure."""
        # Arrange
        mock_config.domain = "test-domain"
        mock_config.campaign_id = "test-campaign-123"
        mock_safe_get.return_value = None

        # Act
        result = get_person("person-123")

        # Assert
        assert result is None

    @patch("app.api.fetch_people._safe_get")
    @patch("app.api.fetch_people.CONFIG")
    def test_get_person_with_special_characters(
        self, mock_config, mock_safe_get, sample_person_data
    ):
        """Test person retrieval with special characters in ID."""
        # Arrange
        mock_config.domain = "test-domain"
        mock_config.campaign_id = "test-campaign-123"
        mock_safe_get.return_value = sample_person_data

        # Act
        result = get_person("person-abc-123-def")

        # Assert
        assert result == sample_person_data
        expected_url = "https://test-domain.actionbuilder.org/api/rest/v1/campaigns/test-campaign-123/people/person-abc-123-def"
        mock_safe_get.assert_called_once_with(expected_url)


class TestFetchConnectionsFromPerson:
    """Tests for the fetch_connections_from_person function."""

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_connections_success(
        self, mock_safe_get, sample_person_data, sample_connections_data
    ):
        """Test successful connections retrieval."""
        # Arrange
        mock_safe_get.return_value = sample_connections_data

        # Act
        result = fetch_connections_from_person(sample_person_data)

        # Assert
        expected_connections = sample_connections_data["_embedded"][
            "action_builder:connections"
        ]
        assert result == expected_connections
        mock_safe_get.assert_called_once_with(
            "https://example.actionbuilder.org/api/rest/v1/people/123/connections"
        )

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_connections_no_links(self, mock_safe_get):
        """Test connections retrieval with no _links in person data."""
        # Arrange
        person_data = {"given_name": "John", "family_name": "Doe"}

        # Act
        result = fetch_connections_from_person(person_data)

        # Assert
        assert result == []
        mock_safe_get.assert_not_called()

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_connections_no_connections_link(self, mock_safe_get):
        """Test connections retrieval with no connections link in person data."""
        # Arrange
        person_data = {
            "given_name": "John",
            "_links": {"other_link": {"href": "https://example.com"}},
        }

        # Act
        result = fetch_connections_from_person(person_data)

        # Assert
        assert result == []
        mock_safe_get.assert_not_called()

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_connections_api_failure(self, mock_safe_get, sample_person_data):
        """Test connections retrieval when API call fails."""
        # Arrange
        mock_safe_get.return_value = None

        # Act
        result = fetch_connections_from_person(sample_person_data)

        # Assert
        assert result == []

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_connections_no_embedded_data(
        self, mock_safe_get, sample_person_data
    ):
        """Test connections retrieval with no embedded connections data."""
        # Arrange
        mock_safe_get.return_value = {"some_other_field": "value"}

        # Act
        result = fetch_connections_from_person(sample_person_data)

        # Assert
        assert result == []


class TestFetchUnitFromConnection:
    """Tests for the fetch_unit_from_connection function."""

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_unit_success(
        self, mock_safe_get, sample_connections_data, sample_unit_data
    ):
        """Test successful unit retrieval from connection."""
        # Arrange
        connections = sample_connections_data["_embedded"]["action_builder:connections"]
        mock_safe_get.return_value = sample_unit_data

        # Act
        result = fetch_unit_from_connection(connections)

        # Assert
        assert result == sample_unit_data
        mock_safe_get.assert_called_once_with(
            "https://example.actionbuilder.org/api/rest/v1/units/456"
        )

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_unit_no_people_units_connection(self, mock_safe_get):
        """Test unit retrieval with no 'People + Units' connection."""
        # Arrange
        connections = [
            {
                "connection_type": "Other Connection",
                "_links": {"osdi:person": {"href": "https://example.com/unit/123"}},
            }
        ]

        # Act
        result = fetch_unit_from_connection(connections)

        # Assert
        assert result is None
        mock_safe_get.assert_not_called()

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_unit_no_person_link(self, mock_safe_get):
        """Test unit retrieval with 'People + Units' connection but no person link."""
        # Arrange
        connections = [
            {
                "connection_type": "People + Units",
                "_links": {"other_link": {"href": "https://example.com/other"}},
            }
        ]

        # Act
        result = fetch_unit_from_connection(connections)

        # Assert
        assert result is None
        mock_safe_get.assert_not_called()

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_unit_api_failure(self, mock_safe_get, sample_connections_data):
        """Test unit retrieval when API call fails."""
        # Arrange
        connections = sample_connections_data["_embedded"]["action_builder:connections"]
        mock_safe_get.return_value = None

        # Act
        result = fetch_unit_from_connection(connections)

        # Assert
        assert result is None

    def test_fetch_unit_empty_connections_list(self):
        """Test unit retrieval with empty connections list."""
        # Act
        result = fetch_unit_from_connection([])

        # Assert
        assert result is None


class TestFetchTaggingsFromConnection:
    """Tests for the fetch_taggings_from_connection function."""

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_taggings_success(
        self, mock_safe_get, sample_connections_data, sample_taggings_data
    ):
        """Test successful taggings retrieval from connection."""
        # Arrange
        connections = sample_connections_data["_embedded"]["action_builder:connections"]
        mock_safe_get.return_value = sample_taggings_data

        # Act
        result = fetch_taggings_from_connection(connections)

        # Assert
        expected_taggings = sample_taggings_data["_embedded"]["osdi:taggings"]
        assert result == expected_taggings
        mock_safe_get.assert_called_once_with(
            "https://example.actionbuilder.org/api/rest/v1/people/123/taggings"
        )

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_taggings_no_people_units_connection(self, mock_safe_get):
        """Test taggings retrieval with no 'People + Units' connection."""
        # Arrange
        connections = [
            {
                "connection_type": "Other Connection",
                "_links": {"osdi:taggings": {"href": "https://example.com/taggings"}},
            }
        ]

        # Act
        result = fetch_taggings_from_connection(connections)

        # Assert
        assert result is None
        mock_safe_get.assert_not_called()

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_taggings_no_taggings_link(self, mock_safe_get):
        """Test taggings retrieval with 'People + Units' connection but no taggings link."""
        # Arrange
        connections = [
            {
                "connection_type": "People + Units",
                "_links": {"osdi:person": {"href": "https://example.com/person"}},
            }
        ]

        # Act
        result = fetch_taggings_from_connection(connections)

        # Assert
        assert result is None
        mock_safe_get.assert_not_called()

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_taggings_api_failure(self, mock_safe_get, sample_connections_data):
        """Test taggings retrieval when API call fails."""
        # Arrange
        connections = sample_connections_data["_embedded"]["action_builder:connections"]
        mock_safe_get.return_value = None

        # Act
        result = fetch_taggings_from_connection(connections)

        # Assert
        assert result == []

    @patch("app.api.fetch_people._safe_get")
    def test_fetch_taggings_no_embedded_data(
        self, mock_safe_get, sample_connections_data
    ):
        """Test taggings retrieval with no embedded taggings data."""
        # Arrange
        connections = sample_connections_data["_embedded"]["action_builder:connections"]
        mock_safe_get.return_value = {"some_other_field": "value"}

        # Act
        result = fetch_taggings_from_connection(connections)

        # Assert
        assert result == []

    def test_fetch_taggings_empty_connections_list(self):
        """Test taggings retrieval with empty connections list."""
        # Act
        result = fetch_taggings_from_connection([])

        # Assert
        assert result is None


class TestParameterizedScenarios:
    """Parameterized tests for various scenarios."""

    @pytest.mark.parametrize(
        "connection_type,should_find",
        [
            ("People + Units", True),
            ("Other Connection", False),
            ("People + Groups", False),
            ("Units + People", False),  # Order matters
        ],
    )
    @patch("app.api.fetch_people._safe_get")
    def test_connection_type_filtering(
        self, mock_safe_get, connection_type, should_find
    ):
        """Test that only 'People + Units' connections are processed."""
        # Arrange
        connections = [
            {
                "connection_type": connection_type,
                "_links": {
                    "osdi:person": {"href": "https://example.com/unit"},
                    "osdi:taggings": {"href": "https://example.com/taggings"},
                },
            }
        ]

        # Simulate realistic API responses
        mock_safe_get.side_effect = [
            {"id": "unit_1"},  # for fetch_unit_from_connection
            {
                "_embedded": {"osdi:taggings": [{"id": "tag_1"}]}
            },  # for fetch_taggings_from_connection
        ]

        # Act
        unit_result = fetch_unit_from_connection(connections)
        taggings_result = fetch_taggings_from_connection(connections)

        # Assert
        if should_find:
            assert unit_result == {"id": "unit_1"}
            assert taggings_result == [{"id": "tag_1"}]
            assert mock_safe_get.call_count == 2
        else:
            assert unit_result is None
            assert taggings_result is None
            mock_safe_get.assert_not_called()


class TestIntegration:
    """Integration-style tests."""

    def test_headers_structure(self):
        """Test that HEADERS contains required fields."""
        assert "OSDI-API-Token" in HEADERS
        assert "Content-Type" in HEADERS
        assert HEADERS["Content-Type"] == "application/json"

    @patch("app.api.fetch_people.CONFIG")
    @patch(
        "app.api.fetch_people.HEADERS",
        {"OSDI-API-Token": "test-key", "Content-Type": "application/json"},
    )
    @patch("app.api.fetch_people.requests.get")
    def test_integration_with_config(self, mock_get, mock_config):
        """Test integration with config values."""
        # Arrange
        mock_config.domain = "test-domain"
        mock_config.campaign_id = "test-campaign"
        mock_config.api_key = "test-key"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Act
        result = get_person("person-123")

        # Assert
        assert result == {"test": "data"}
        expected_url = "https://test-domain.actionbuilder.org/api/rest/v1/campaigns/test-campaign/people/person-123"
        expected_headers = {
            "OSDI-API-Token": "test-key",
            "Content-Type": "application/json",
        }
        mock_get.assert_called_once_with(expected_url, headers=expected_headers)
