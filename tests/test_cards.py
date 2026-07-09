from app.services.card_service import compute_new_position


def test_create_card_success(client):
    res = client.post("/api/cards", json={"title": "Login button does nothing"})
    assert res.status_code == 201
    body = res.get_json()
    assert body["title"] == "Login button does nothing"
    assert body["status"] == "Open"
    assert body["severity"] == "minor"
    assert body["position"] == 1.0


def test_create_card_requires_title(client):
    res = client.post("/api/cards", json={"title": "  "})
    assert res.status_code == 400


def test_create_card_rejects_bad_status(client):
    res = client.post("/api/cards", json={"title": "x", "status": "Bogus"})
    assert res.status_code == 400


def test_list_cards_empty(client):
    res = client.get("/api/cards")
    assert res.status_code == 200
    assert res.get_json() == []


def test_get_card_not_found(client):
    res = client.get("/api/cards/999")
    assert res.status_code == 404


def test_update_card_fields(client):
    created = client.post("/api/cards", json={"title": "Crash on save"}).get_json()
    res = client.patch(f"/api/cards/{created['id']}", json={"severity": "critical", "assignee": "mahmoud"})
    assert res.status_code == 200
    body = res.get_json()
    assert body["severity"] == "critical"
    assert body["assignee"] == "mahmoud"
    # untouched fields stay as-is
    assert body["title"] == "Crash on save"


def test_update_card_not_found(client):
    res = client.patch("/api/cards/999", json={"severity": "critical"})
    assert res.status_code == 404


def test_update_card_rejects_bad_severity(client):
    created = client.post("/api/cards", json={"title": "x"}).get_json()
    res = client.patch(f"/api/cards/{created['id']}", json={"severity": "apocalyptic"})
    assert res.status_code == 400


def test_delete_card(client):
    created = client.post("/api/cards", json={"title": "Delete me"}).get_json()
    res = client.delete(f"/api/cards/{created['id']}")
    assert res.status_code == 204
    assert client.get(f"/api/cards/{created['id']}").status_code == 404


def test_new_card_appends_to_bottom_of_its_column(client):
    first = client.post("/api/cards", json={"title": "A"}).get_json()
    second = client.post("/api/cards", json={"title": "B"}).get_json()
    assert second["position"] > first["position"]


def test_move_card_to_new_column_and_position(client):
    a = client.post("/api/cards", json={"title": "A", "status": "In Progress"}).get_json()
    b = client.post("/api/cards", json={"title": "B", "status": "In Progress"}).get_json()

    # move a new card between a and b in the "Testing" column
    c = client.post("/api/cards", json={"title": "C", "status": "Testing"}).get_json()

    res = client.patch(
        f"/api/cards/{c['id']}",
        json={"status": "In Progress", "before_id": a["id"], "after_id": b["id"]},
    )
    body = res.get_json()
    assert body["status"] == "In Progress"
    assert a["position"] < body["position"] < b["position"]


# ---- fractional positioning unit tests (no HTTP, pure logic) ----

def test_compute_new_position_empty_column():
    assert compute_new_position(None, None) == 1.0


def test_compute_new_position_top_of_column():
    assert compute_new_position(None, 4.0) == 2.0


def test_compute_new_position_bottom_of_column():
    assert compute_new_position(3.0, None) == 4.0


def test_compute_new_position_between_two_cards():
    assert compute_new_position(1.0, 2.0) == 1.5
