import os
from unittest import mock
from restaurant_finder import create_app
from flask import json


class DummyGMaps:
    def __init__(self, results=None, location=None):
        self.results = results or []
        self.location = location or {"location": {"lat": 1.0, "lng": 2.0}}

    def places_nearby(self, **kwargs):
        return {"status": "OK", "results": self.results}

    def geolocate(self):
        return self.location


def create_test_client(results=None, location=None):
    os.environ["GOOGLE_API_KEY"] = "AIzaTEST"
    with mock.patch("googlemaps.Client", return_value=DummyGMaps(results, location)):
        app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_index_route():
    client = create_test_client()
    resp = client.get("/")
    assert resp.status_code == 200


def test_search_restaurants_invalid_radius_small():
    client = create_test_client()
    resp = client.post(
        "/search_restaurants",
        json={"lat": 0, "lng": 0, "radius": 500},
    )
    data = resp.get_json()
    assert "検索半径は1km以上" in data["error"]


def test_search_restaurants_invalid_radius_large():
    client = create_test_client()
    resp = client.post(
        "/search_restaurants",
        json={"lat": 0, "lng": 0, "radius": 60000},
    )
    data = resp.get_json()
    assert "検索半径が大きすぎます" in data["error"]


def test_search_restaurants_success():
    results = [
        {
            "place_id": "1",
            "name": "Test Resto",
            "vicinity": "Somewhere",
            "rating": 4.5,
            "geometry": {"location": {"lat": 35.608, "lng": 140.107}},
        }
    ]
    client = create_test_client(results=results)
    resp = client.post(
        "/search_restaurants",
        json={"lat": 35.607, "lng": 140.106, "radius": 1000},
    )
    data = resp.get_json()
    assert len(data["restaurants"]) == 1
    assert data["restaurants"][0]["name"] == "Test Resto"


def test_get_current_location():
    location = {"location": {"lat": 10, "lng": 20}}
    client = create_test_client(location=location)
    resp = client.get("/get_current_location")
    data = resp.get_json()
    assert data["location"] == location["location"]
