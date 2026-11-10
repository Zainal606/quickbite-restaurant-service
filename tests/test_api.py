def _create_restaurant(client, **overrides):
    body = {"name": "Spice Route", "cuisine": "Indian", "city": "Dubai"} | overrides
    response = client.post("/restaurants", json=body)
    assert response.status_code == 201
    return response.json()


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "UP"
    assert body["service"] == "restaurant-service"


def test_register_and_list_restaurants(client):
    _create_restaurant(client)
    _create_restaurant(client, name="Pasta Corner", cuisine="Italian", city="Abu Dhabi")

    assert len(client.get("/restaurants").json()) == 2
    dubai = client.get("/restaurants", params={"city": "dubai"}).json()
    assert [r["name"] for r in dubai] == ["Spice Route"]


def test_menu_lifecycle(client):
    restaurant = _create_restaurant(client)
    rid = restaurant["id"]

    item = client.post(f"/restaurants/{rid}/menu-items", json={"name": "Paneer Tikka", "price": 28.5}).json()
    assert item["is_available"] is True

    updated = client.patch(f"/menu-items/{item['id']}", json={"price": 30, "is_available": False}).json()
    assert updated["price"] == 30
    assert updated["is_available"] is False

    detail = client.get(f"/restaurants/{rid}").json()
    assert detail["menu"][0]["name"] == "Paneer Tikka"

    assert client.delete(f"/menu-items/{item['id']}").status_code == 204
    assert client.get(f"/restaurants/{rid}/menu").json() == []


def test_close_restaurant(client):
    rid = _create_restaurant(client)["id"]
    body = client.patch(f"/restaurants/{rid}/status", json={"is_open": False}).json()
    assert body["is_open"] is False


def test_not_found_and_validation(client):
    assert client.get("/restaurants/999").status_code == 404
    assert client.post("/restaurants/999/menu-items", json={"name": "x", "price": 1}).status_code == 404
    rid = _create_restaurant(client)["id"]
    assert client.post(f"/restaurants/{rid}/menu-items", json={"name": "Free", "price": 0}).status_code == 422
