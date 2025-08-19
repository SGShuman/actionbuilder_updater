from unittest.mock import patch

import pytest

import app.sync.run_status_type_sync as sync


@pytest.fixture
def fake_person():
    return {"identifiers": ["actionbuilder:person:123"]}


def test_dict_to_csv_filters_fields_and_inactive():
    data = {
        "1": sync.PersonUnitInfo(
            uuid="1",
            unit_name="Unit A",
            membership_status_tag_id="s1",
            membership_type_tag_id="t1",
            membership_status="Active",
            membership_type="Full",
            inactive=False,
        ),
        "2": sync.PersonUnitInfo(
            uuid="2",
            unit_name="Unit B",
            membership_status_tag_id="s2",
            membership_type_tag_id="t2",
            membership_status="Inactive",
            membership_type="Associate",
            inactive=True,
        ),
    }
    csv_content, row_count = sync.dict_to_csv(data)

    assert "membership_status_tag_id" not in csv_content
    assert "membership_type_tag_id" not in csv_content
    assert "membership_status" not in csv_content
    assert "inactive" not in csv_content
    assert "1" in csv_content
    assert "2" not in csv_content
    assert row_count == 1


def test_get_person_current_tags_extracts_correct_tags():
    fake_tags = [
        {
            "action_builder:field": "Membership Status",
            "action_builder:name": "Active",
            "identifiers": ["tag:status:111"],
        },
        {
            "action_builder:field": "Membership Type",
            "action_builder:name": "Full",
            "identifiers": ["tag:type:222"],
        },
    ]
    with patch.object(sync, "get_all_tags", return_value=fake_tags):
        result = sync.get_person_current_tags("123")

    assert result["status"]["tag_name"] == "Active"
    assert result["status"]["tag_id"] == "111"
    assert result["type"]["tag_name"] == "Full"
    assert result["type"]["tag_id"] == "222"


def test_extract_connection_membership_info_returns_expected_tuple():
    taggings = [
        {
            "action_builder:field": "Membership Status",
            "action_builder:name": "Active",
            "identifiers": ["tag:status:aaa"],
        },
        {
            "action_builder:field": "Membership Type",
            "action_builder:name": "Associate",
            "identifiers": ["tag:type:bbb"],
        },
    ]
    status, status_id, type_val, type_id = sync.extract_connection_membership_info(
        taggings
    )
    assert status == "Active"
    assert status_id == "aaa"
    assert type_val == "Associate"
    assert type_id == "bbb"


def test_process_person_returns_none_if_no_identifiers():
    result = sync.process_person({}, verbose=False)
    assert result is None


@patch.object(sync, "get_person")
@patch.object(sync, "fetch_connections_from_person")
@patch.object(sync, "fetch_unit_from_connection")
@patch.object(sync, "fetch_taggings_from_connection")
@patch.object(sync, "get_person_current_tags")
def test_process_person_detects_difference(
    mock_tags,
    mock_fetch_tags,
    mock_fetch_unit,
    mock_fetch_conn,
    mock_get_person,
    fake_person,
):
    mock_get_person.return_value = {"browser_url": "url"}
    mock_fetch_conn.return_value = {"connection": "dummy"}
    mock_fetch_unit.return_value = {"action_builder:name": "UnitX"}
    mock_fetch_tags.return_value = [
        {
            "action_builder:field": "Membership Status",
            "action_builder:name": "Active",
            "identifiers": ["tag:status:1"],
        },
        {
            "action_builder:field": "Membership Type",
            "action_builder:name": "Full",
            "identifiers": ["tag:type:2"],
        },
    ]
    mock_tags.return_value = {
        "status": {"tag_id": "1", "tag_name": "Inactive"},
        "type": {"tag_id": "2", "tag_name": "Probationary"},
    }

    result = sync.process_person(fake_person, verbose=False)
    assert isinstance(result, sync.PersonUnitInfo)
    assert result.unit_name == "UnitX"
    assert result.inactive is False


def test_process_people_batch_wraps_process_person(monkeypatch, fake_person):
    called = {}

    def fake_process(p, verbose=True):
        called["x"] = True
        return sync.PersonUnitInfo(
            uuid="123",
            unit_name="U",
            membership_status_tag_id="a",
            membership_type_tag_id="b",
            membership_status="Active",
            membership_type="Full",
            inactive=False,
        )

    monkeypatch.setattr(sync, "process_person", fake_process)
    batch = [(0, fake_person)]
    results = sync.process_people_batch(batch, verbose=False)
    assert results[0][0] == 0
    assert isinstance(results[0][1], sync.PersonUnitInfo)
    assert called


@patch.object(sync, "delete_tagging")
def test_delete_tag_for_person_success(mock_delete):
    mock_delete.return_value = True
    assert sync.delete_tag_for_person("123", "t1", "status") is True


@patch.object(sync, "delete_tagging", side_effect=Exception("boom"))
def test_delete_tag_for_person_failure(mock_delete):
    assert sync.delete_tag_for_person("123", "t1", "status") is False


def test_delete_outdated_tags_runs_parallel(monkeypatch):
    people_map = {
        "123": sync.PersonUnitInfo(
            uuid="123",
            unit_name="U",
            membership_status_tag_id="s1",
            membership_type_tag_id="t1",
            membership_status="Active",
            membership_type="Full",
            inactive=False,
        )
    }

    monkeypatch.setattr(sync, "delete_tag_for_person", lambda *a, **k: True)

    # Should not raise and should log something
    sync.delete_outdated_tags(people_map, max_workers=2)


@patch.object(sync, "send_email")
def test_main_sends_email_when_data(mock_email, monkeypatch):
    # run_today(today: int) expects one argument
    monkeypatch.setattr(sync, "run_today", lambda today: True)

    fake_map = {
        "123": sync.PersonUnitInfo(
            uuid="123",
            unit_name="U",
            membership_status_tag_id="s1",
            membership_type_tag_id="t1",
            membership_status="Active",
            membership_type="Full",
            inactive=False,
        )
    }

    # Allow positional args
    monkeypatch.setattr(sync, "build_people_unit_map", lambda *a, **k: fake_map)
    monkeypatch.setattr(sync, "delete_outdated_tags", lambda *a, **k: None)

    sync.main(scheduled=True, max_workers=1, batch_size=1)
    assert mock_email.called
