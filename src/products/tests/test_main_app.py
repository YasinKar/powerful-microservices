from fastapi.routing import APIRoute

from main import app, custom_generate_unique_id


def test_custom_generate_unique_id_uses_tag_and_name():
    route = APIRoute(path="/x", endpoint=lambda: None, methods=["GET"], name="read-x", tags=["Tag"])
    assert custom_generate_unique_id(route) == "Tag-read-x"


def test_openapi_endpoint_available(client):
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "products_service"
