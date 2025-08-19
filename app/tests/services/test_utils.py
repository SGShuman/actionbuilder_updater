import smtplib
from datetime import datetime
from unittest import mock

import pytest
import requests

from app.services.utils import is_first_of_month, retry_email, retry_request, run_today

# ---------------------------
# Tests for retry_request
# ---------------------------


def test_retry_success_on_first_try():
    @retry_request(max_attempts=3)
    def always_succeeds():
        return "ok"

    assert always_succeeds() == "ok"


def test_retry_raises_after_max_attempts():
    @retry_request(max_attempts=3, backoff=0)
    def always_fails():
        raise requests.RequestException("fail")

    with pytest.raises(requests.RequestException):
        always_fails()


def test_retry_retries_on_false_when_retry_if_false_true():
    call_count = {"count": 0}

    @retry_request(max_attempts=3, backoff=0, retry_if_false=True)
    def returns_false_then_true():
        call_count["count"] += 1
        return True if call_count["count"] == 3 else False

    with mock.patch("time.sleep", return_value=None):
        assert returns_false_then_true() is True
    assert call_count["count"] == 3


def test_retry_does_not_retry_on_false_when_retry_if_false_false():
    call_count = {"count": 0}

    @retry_request(max_attempts=3, backoff=0, retry_if_false=False)
    def always_false():
        call_count["count"] += 1
        return False

    with mock.patch("time.sleep", return_value=None):
        assert always_false() is False
    assert call_count["count"] == 1


# ---------------------------
# Tests for is_first_of_month
# ---------------------------


def test_is_first_of_month_true():
    fake_date = datetime(2025, 8, 1)
    with mock.patch("app.services.utils.datetime") as mock_datetime:
        mock_datetime.today.return_value = fake_date
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        assert is_first_of_month() is True


def test_is_first_of_month_false():
    fake_date = datetime(2025, 8, 18)
    with mock.patch("app.services.utils.datetime") as mock_datetime:
        mock_datetime.today.return_value = fake_date
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        assert is_first_of_month() is False


def test_run_today_matches():
    # Mock datetime.today() to return a specific date
    mock_date = datetime(2025, 8, 18)
    with mock.patch("app.services.utils.datetime") as mock_datetime:
        mock_datetime.today.return_value = mock_date
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        assert run_today(18) is True


def test_run_today_does_not_match():
    mock_date = datetime(2025, 8, 18)
    with mock.patch("app.services.utils.datetime") as mock_datetime:
        mock_datetime.today.return_value = mock_date
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        assert run_today(5) is False


def test_retry_email_success_on_first_try():
    mock_func = mock.Mock(return_value="sent")
    decorated = retry_email()(mock_func)

    result = decorated()

    assert result == "sent"
    assert mock_func.call_count == 1


def test_retry_email_retries_on_exception():
    mock_func = mock.Mock(side_effect=[smtplib.SMTPException("fail"), "sent"])
    decorated = retry_email(max_attempts=3, base_delay=0.1, jitter=False)(mock_func)

    with mock.patch("app.services.utils.sleep") as mock_sleep:
        result = decorated()

    assert result == "sent"
    assert mock_func.call_count == 2
    mock_sleep.assert_called()  # sleep was called once between retries


def test_retry_email_fails_after_max_attempts():
    mock_func = mock.Mock(side_effect=smtplib.SMTPException("fail"))
    decorated = retry_email(max_attempts=3, base_delay=0.1, jitter=False)(mock_func)

    with mock.patch("app.services.utils.sleep") as mock_sleep:
        with pytest.raises(smtplib.SMTPException):
            decorated()

    assert mock_func.call_count == 3
    mock_sleep.assert_called()  # sleep was called between retries


def test_retry_email_does_not_retry_unexpected_exception():
    class CustomError(Exception):
        pass

    mock_func = mock.Mock(side_effect=CustomError("oops"))
    decorated = retry_email(max_attempts=3)(mock_func)

    with pytest.raises(CustomError):
        decorated()

    assert mock_func.call_count == 1


def test_retry_email_jitter_applied():
    mock_func = mock.Mock(side_effect=[smtplib.SMTPException("fail"), "sent"])
    decorated = retry_email(max_attempts=2, base_delay=1.0, jitter=True)(mock_func)

    with (
        mock.patch("app.services.utils.sleep") as mock_sleep,
        mock.patch("app.services.utils.uniform", return_value=1.05),
    ):  # jitter factor
        result = decorated()

    assert result == "sent"
    # Expected delay: base_delay * exponential_base^(attempt-1) * jitter factor
    mock_sleep.assert_called_once()
    delay_arg = mock_sleep.call_args[0][0]
    assert 1.0 <= delay_arg <= 1.1  # 5% jitter applied
