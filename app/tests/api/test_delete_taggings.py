from unittest.mock import MagicMock, patch

import pytest
import requests

# Import the module under test
from app.api.delete_taggings import BASE_URL, HEADERS, delete_tagging


@pytest.fixture
def person_id():
    """Fixture for person ID."""
    return "7edd9555-3ff9-4833-9f3f-fdf4a064e8ec"


@pytest.fixture
def tagging_id():
    """Fixture for tagging ID."""
    return "6f3136ca-8d68-4c84-b22c-93960ae6adac"


@pytest.fixture
def expected_url(person_id, tagging_id):
    """Fixture for expected URL."""
    return f"{BASE_URL}{person_id}/taggings/{tagging_id}"


class TestDeleteTagging:
    """Test cases for the delete_tagging function."""

    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_success_200(
        self, mock_delete, person_id, tagging_id, expected_url
    ):
        """Test successful deletion with 200 status code."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is True
        mock_delete.assert_called_once_with(expected_url, headers=HEADERS)

    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_success_204(
        self, mock_delete, person_id, tagging_id, expected_url
    ):
        """Test successful deletion with 204 status code."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is True
        mock_delete.assert_called_once_with(expected_url, headers=HEADERS)

    @patch("builtins.print")
    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_failure_404(
        self, mock_delete, mock_print, person_id, tagging_id, expected_url
    ):
        """Test failed deletion with 404 status code."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_delete.return_value = mock_response

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is False
        assert mock_delete.call_count == 3
        mock_delete.assert_called_with(expected_url, headers=HEADERS)

        mock_print.assert_called_with(
            f"Failed to delete tagging {tagging_id} for person {person_id}: 404 Not Found"
        )

    @patch("builtins.print")
    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_failure_401(
        self, mock_delete, mock_print, person_id, tagging_id, expected_url
    ):
        """Test failed deletion with 401 unauthorized status code."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_delete.return_value = mock_response

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is False
        assert mock_delete.call_count == 3
        mock_delete.assert_called_with(expected_url, headers=HEADERS)
        # mock_print.assert_called_once_with(
        #     f"Failed to delete tagging {tagging_id} for person {person_id}: 401 Unauthorized"
        # )

    @patch("builtins.print")
    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_failure_500(
        self, mock_delete, mock_print, person_id, tagging_id, expected_url
    ):
        """Test failed deletion with 500 server error."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_delete.return_value = mock_response

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is False
        assert mock_delete.call_count == 3
        mock_delete.assert_called_with(expected_url, headers=HEADERS)
        # mock_print.assert_called_once_with(
        #     f"Failed to delete tagging {tagging_id} for person {person_id}: 500 Internal Server Error"
        # )

    @patch("builtins.print")
    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_connection_error(
        self, mock_delete, mock_print, person_id, tagging_id, expected_url
    ):
        """Test deletion with connection error."""
        # Arrange
        mock_delete.side_effect = requests.ConnectionError("Connection failed")

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is False
        assert mock_delete.call_count == 3
        mock_delete.assert_called_with(expected_url, headers=HEADERS)
        # mock_print.assert_called_once_with(
        #     f"Error deleting tagging {tagging_id} for person {person_id}: Connection failed"
        # )

    @patch("builtins.print")
    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_timeout_error(
        self, mock_delete, mock_print, person_id, tagging_id, expected_url
    ):
        """Test deletion with timeout error."""
        # Arrange
        mock_delete.side_effect = requests.Timeout("Request timed out")

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is False
        assert mock_delete.call_count == 3
        mock_delete.assert_called_with(expected_url, headers=HEADERS)
        # mock_print.assert_called_once_with(
        #     f"Error deleting tagging {tagging_id} for person {person_id}: Request timed out"
        # )

    @patch("builtins.print")
    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_http_error(
        self, mock_delete, mock_print, person_id, tagging_id, expected_url
    ):
        """Test deletion with HTTP error."""
        # Arrange
        mock_delete.side_effect = requests.HTTPError("HTTP Error occurred")

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is False
        assert mock_delete.call_count == 3
        mock_delete.assert_called_with(expected_url, headers=HEADERS)
        # mock_print.assert_called_once_with(
        #     f"Error deleting tagging {tagging_id} for person {person_id}: HTTP Error occurred"
        # )

    @patch("builtins.print")
    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_generic_request_exception(
        self, mock_delete, mock_print, person_id, tagging_id, expected_url
    ):
        """Test deletion with generic request exception."""
        # Arrange
        mock_delete.side_effect = requests.RequestException("Generic request error")

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is False
        assert mock_delete.call_count == 3
        mock_delete.assert_called_with(expected_url, headers=HEADERS)
        # mock_print.assert_called_once_with(
        #     f"Error deleting tagging {tagging_id} for person {person_id}: Generic request error"
        # )

    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_with_empty_strings(self, mock_delete):
        """Test deletion with empty string IDs."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        person_id = ""
        tagging_id = ""
        expected_url = f"{BASE_URL}/taggings/"

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is True
        mock_delete.assert_called_once_with(expected_url, headers=HEADERS)

    @patch("app.api.delete_taggings.requests.delete")
    def test_delete_tagging_with_special_characters(self, mock_delete):
        """Test deletion with special characters in IDs."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        person_id = "test-person-123"
        tagging_id = "test_tagging_456"
        expected_url = f"{BASE_URL}{person_id}/taggings/{tagging_id}"

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is True
        mock_delete.assert_called_once_with(expected_url, headers=HEADERS)

    def test_base_url_construction(self):
        """Test that BASE_URL is constructed correctly."""
        assert "/api/rest/v1/campaigns/" in BASE_URL
        assert "/people/" in BASE_URL

    def test_headers_structure(self):
        """Test that HEADERS contains required fields."""
        assert "OSDI-API-Token" in HEADERS
        assert "Content-Type" in HEADERS
        assert HEADERS["Content-Type"] == "application/json"


class TestDeleteTaggingParameterized:
    """Parameterized tests for different scenarios."""

    @pytest.mark.parametrize("status_code", [200, 204])
    @patch("app.api.delete_taggings.requests.delete")
    def test_successful_status_codes(
        self, mock_delete, status_code, person_id, tagging_id
    ):
        """Test that both 200 and 204 status codes are treated as success."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_delete.return_value = mock_response

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is True

    @pytest.mark.parametrize(
        "status_code,status_text",
        [
            (400, "Bad Request"),
            (401, "Unauthorized"),
            (403, "Forbidden"),
            (404, "Not Found"),
            (500, "Internal Server Error"),
            (502, "Bad Gateway"),
            (503, "Service Unavailable"),
        ],
    )
    @patch("builtins.print")
    @patch("app.api.delete_taggings.requests.delete")
    def test_error_status_codes(
        self, mock_delete, mock_print, status_code, status_text, person_id, tagging_id
    ):
        """Test various HTTP error status codes."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = status_text
        mock_delete.return_value = mock_response

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is False
        assert mock_print.call_count == 5
        mock_print.assert_called_with(
            f"Failed to delete tagging {tagging_id} for person {person_id}: {status_code} {status_text}"
        )

    @pytest.mark.parametrize(
        "exception_class,error_message",
        [
            (requests.ConnectionError, "Connection failed"),
            (requests.Timeout, "Request timed out"),
            (requests.HTTPError, "HTTP Error occurred"),
            (requests.RequestException, "Generic request error"),
        ],
    )
    @patch("builtins.print")
    @patch("app.api.delete_taggings.requests.delete")
    def test_request_exceptions(
        self,
        mock_delete,
        mock_print,
        exception_class,
        error_message,
        person_id,
        tagging_id,
    ):
        """Test various request exceptions."""
        # Arrange
        mock_delete.side_effect = exception_class(error_message)

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is False
        assert mock_print.call_count == 5
        mock_print.assert_called_with(
            f"Error deleting tagging {tagging_id} for person {person_id}: {error_message}"
        )


class TestDeleteTaggingIntegration:
    """Integration-style tests that test the full flow."""

    def test_url_construction_with_config(self):
        """Test that URL is constructed correctly with config values."""
        with (
            patch("app.api.delete_taggings.CONFIG") as mock_config,
            patch(
                "app.api.delete_taggings.BASE_URL",
                "https://test-domain.actionbuilder.org/api/rest/v1/campaigns/test-campaign-123/people/",
            ),
            patch(
                "app.api.delete_taggings.HEADERS",
                {"OSDI-API-Token": "test-api-key", "Content-Type": "application/json"},
            ),
            patch("app.api.delete_taggings.requests.delete") as mock_delete,
        ):
            # Arrange
            mock_config.domain = "test-domain"
            mock_config.campaign_id = "test-campaign-123"
            mock_config.api_key = "test-api-key"

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_delete.return_value = mock_response

            person_id = "person-123"
            tagging_id = "tagging-456"

            # Act
            result = delete_tagging(person_id, tagging_id)

            # Assert
            assert result is True
            expected_url = "https://test-domain.actionbuilder.org/api/rest/v1/campaigns/test-campaign-123/people/person-123/taggings/tagging-456"
            expected_headers = {
                "OSDI-API-Token": "test-api-key",
                "Content-Type": "application/json",
            }

            mock_delete.assert_called_once_with(expected_url, headers=expected_headers)

    @patch("app.api.delete_taggings.requests.delete")
    def test_function_uses_module_constants(self, mock_delete):
        """Test that the function uses the BASE_URL and HEADERS from the module."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        person_id = "test-person"
        tagging_id = "test-tagging"

        # Act
        result = delete_tagging(person_id, tagging_id)

        # Assert
        assert result is True
        # Verify it used the actual BASE_URL and HEADERS from the module
        expected_url = f"{BASE_URL}test-person/taggings/test-tagging"
        mock_delete.assert_called_once_with(expected_url, headers=HEADERS)


# Test configuration for pytest
pytest_plugins = []


# Note: All tests use explicit mocking to prevent real HTTP calls
