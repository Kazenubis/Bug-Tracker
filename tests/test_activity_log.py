def test_creating_card_logs_created_event(client):
    card = client.post("/api/cards", json={"title": "New bug"}).get_json()
    res = client.get(f"/api/cards/{card['id']}/activity")
    assert res.status_code == 200
    entries = res.get_json()
    assert len(entries) == 1
    assert entries[0]["event_type"] == "created"


def test_status_change_is_logged(client):
    card = client.post("/api/cards", json={"title": "Bug"}).get_json()
    client.patch(f"/api/cards/{card['id']}", json={"status": "In Progress"})

    entries = client.get(f"/api/cards/{card['id']}/activity").get_json()
    field_updates = [e for e in entries if e["event_type"] == "field_update"]
    assert len(field_updates) == 1
    assert field_updates[0]["field"] == "status"
    assert field_updates[0]["from_value"] == "Open"
    assert field_updates[0]["to_value"] == "In Progress"


def test_multiple_field_changes_in_one_patch_log_separately(client):
    card = client.post("/api/cards", json={"title": "Bug"}).get_json()
    client.patch(
        f"/api/cards/{card['id']}",
        json={"severity": "critical", "assignee": "mahmoud"},
    )

    entries = client.get(f"/api/cards/{card['id']}/activity").get_json()
    fields_changed = {e["field"] for e in entries if e["event_type"] == "field_update"}
    assert fields_changed == {"severity", "assignee"}


def test_noop_update_does_not_create_log_entry(client):
    card = client.post("/api/cards", json={"title": "Bug", "severity": "minor"}).get_json()
    client.patch(f"/api/cards/{card['id']}", json={"severity": "minor"})

    entries = client.get(f"/api/cards/{card['id']}/activity").get_json()
    field_updates = [e for e in entries if e["event_type"] == "field_update"]
    assert len(field_updates) == 0


def test_untracked_field_change_not_logged(client):
    card = client.post("/api/cards", json={"title": "Bug"}).get_json()
    client.patch(f"/api/cards/{card['id']}", json={"description": "more detail"})

    entries = client.get(f"/api/cards/{card['id']}/activity").get_json()
    field_updates = [e for e in entries if e["event_type"] == "field_update"]
    assert len(field_updates) == 0


def test_activity_not_found_for_missing_card(client):
    res = client.get("/api/cards/999/activity")
    assert res.status_code == 404


def test_deleting_card_cascades_activity_log(client, db):
    from app.models import ActivityLog

    card = client.post("/api/cards", json={"title": "Bug"}).get_json()
    client.delete(f"/api/cards/{card['id']}")

    remaining = db.session.query(ActivityLog).filter_by(card_id=card["id"]).count()
    assert remaining == 0
