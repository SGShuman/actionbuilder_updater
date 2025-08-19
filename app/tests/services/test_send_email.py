from unittest.mock import MagicMock, patch

import pytest

from app.services import send_email as email_module


# Mock CONFIG object for testing
class MockConfig:
    smtp_username = "test@example.com"
    smtp_password = "password123"
    smtp_server = "smtp.example.com"
    smtp_port = 587


@pytest.fixture(autouse=True)
def patch_config_and_recipients():
    with (
        patch.object(email_module, "CONFIG", MockConfig),
        patch(
            "app.services.send_email.get_recipient_emails",
            return_value=["recipient@example.com"],
        ),
    ):
        yield


@pytest.fixture
def mock_smtp():
    with patch("smtplib.SMTP") as mock_smtp_cls:
        instance = MagicMock()
        mock_smtp_cls.return_value.__enter__.return_value = instance
        yield instance


def test_send_email_no_attachment(mock_smtp):
    email_module.send_email(subject="Test Subject", html_content="<p>Hello</p>")

    # Ensure SMTP login and send_message called
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with(
        MockConfig.smtp_username, MockConfig.smtp_password
    )
    assert mock_smtp.send_message.call_count == 1

    sent_msg = mock_smtp.send_message.call_args[0][0]
    assert sent_msg["Subject"] == "Test Subject"
    assert sent_msg.get_content_type() == "text/html"
    assert "Hello" in sent_msg.get_content()


def test_send_email_with_attachment(mock_smtp):
    csv_data = "name,email\nAlice,alice@example.com"
    email_module.send_email(csv_content=csv_data)

    sent_msg = mock_smtp.send_message.call_args[0][0]

    attachments = list(sent_msg.iter_attachments())
    assert len(attachments) == 1
    attachment = attachments[0]
    assert attachment.get_filename().startswith("ActionBuilder_Sync_Export_")
    assert attachment.get_content_type() == "text/csv"
    # Compare directly as string
    assert attachment.get_content() == csv_data


def test_missing_smtp_credentials():
    with patch.object(email_module, "CONFIG", MockConfig) as cfg:
        cfg.smtp_username = None
        cfg.smtp_password = None
        with pytest.raises(ValueError, match="SMTP credentials not set"):
            email_module.send_email()
