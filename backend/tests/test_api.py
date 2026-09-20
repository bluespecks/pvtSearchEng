import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import httpx

from backend.app.main import app

client = TestClient(app)


class MockResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            request = httpx.Request("GET", "http://testserver")
            raise httpx.HTTPStatusError("Error", request=request, response=MagicMock())


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "PvtSearchEng API"
    assert data["status"] == "online"
    assert data["version"] == "0.1.0"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_empty_search():
    response = client.get("/search?q=")
    assert response.status_code == 422


@patch("httpx.AsyncClient.get")
def test_normal_search(mock_get):
    mock_get.return_value = MockResponse({
        "results": [
            {
                "title": "Python Tutorial",
                "url": "https://docs.python.org/3/tutorial/",
                "content": "Official Python tutorial content.",
                "engines": ["google", "bing"],
                "score": 1,
            }
        ]
    })

    response = client.get("/search?q=python")
    assert response.status_code == 200
    data = response.json()

    assert data["query"] == "python"
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 1

    res = data["results"][0]
    assert "title" in res
    assert "url" in res
    assert "description" in res
    assert "source" in res
    assert "score" in res


@patch("httpx.AsyncClient.get")
def test_deduplication(mock_get):
    mock_get.return_value = MockResponse({
        "results": [
            {
                "title": "A",
                "url": "https://example.com/same",
                "content": "A",
                "engines": ["engineA"],
            },
            {
                "title": "B",
                "url": "https://example.com/same",
                "content": "B",
                "engines": ["engineB"],
            }
        ]
    })

    response = client.get("/search?q=test")
    data = response.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["url"] == "https://example.com/same"


@patch("httpx.AsyncClient.get")
def test_source_merging(mock_get):
    mock_get.return_value = MockResponse({
        "results": [
            {
                "title": "A",
                "url": "https://example.com/same",
                "content": "A",
                "engines": ["brave"],
            },
            {
                "title": "B",
                "url": "https://example.com/same",
                "content": "B",
                "engines": ["duckduckgo"],
            },
            {
                "title": "C",
                "url": "https://example.com/same",
                "content": "C",
                "engines": ["brave", "google"],
            }
        ]
    })

    response = client.get("/search?q=test")
    data = response.json()
    assert len(data["results"]) == 1

    source_str = data["results"][0]["source"]
    sources = set(source_str.split(", "))
    assert sources == {"brave", "duckduckgo", "google"}


@patch("httpx.AsyncClient.get")
def test_ranking(mock_get):
    mock_get.return_value = MockResponse({
        "results": [
            {
                "title": "Some completely unrelated tutorial",
                "url": "https://example.com/1",
                "content": "Does not contain the query.",
                "engines": ["google"],
            },
            {
                "title": "The Ultimate Python Guide",
                "url": "https://example.com/2",
                "content": "Learn python today.",
                "engines": ["google"],
            }
        ]
    })

    response = client.get("/search?q=python")
    data = response.json()

    assert len(data["results"]) == 2
    # The one with 'python' in title/description should score highest and be first
    assert data["results"][0]["url"] == "https://example.com/2"


@patch("httpx.AsyncClient.get")
def test_debug_ranking(mock_get):
    mock_get.return_value = MockResponse({
        "results": [
            {
                "title": "Python Tutorial",
                "url": "https://example.com/1",
                "content": "A tutorial.",
                "engines": ["google"],
            }
        ]
    })

    # Debug true
    response = client.get("/search?q=python&debug=true")
    data = response.json()
    assert "ranking" in data["results"][0]
    ranking = data["results"][0]["ranking"]
    assert "phrase_title" in ranking
    assert "word_description" in ranking

    # Debug false
    response_normal = client.get("/search?q=python")
    data_normal = response_normal.json()
    assert "ranking" not in data_normal["results"][0]


@patch("httpx.AsyncClient.get")
def test_searxng_network_failure(mock_get):
    mock_get.side_effect = httpx.ConnectError("Network is unreachable")
    response = client.get("/search?q=python")
    assert response.status_code == 502
    assert response.json() == {"detail": "Search service unavailable"}


@patch("httpx.AsyncClient.get")
def test_searxng_invalid_json(mock_get):
    mock_get.return_value = MockResponse(ValueError("Invalid JSON"))
    response = client.get("/search?q=python")
    assert response.status_code == 502
    assert response.json() == {"detail": "Search service unavailable"}


@patch("httpx.AsyncClient.get")
def test_searxng_malformed_schema(mock_get):
    # Returns an object without 'results' key
    mock_get.return_value = MockResponse({"bad": "data"})
    response = client.get("/search?q=python")
    assert response.status_code == 502
    assert response.json() == {"detail": "Search service unavailable"}
