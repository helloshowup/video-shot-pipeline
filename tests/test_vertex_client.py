import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.vertex_client import poll_video_generation, start_video_generation


class MockCreds:
    def __init__(self, token="tok"):
        self.token = token

    def refresh(self, request):
        return None


def setup_google_auth(mock_default):
    mock_creds = MockCreds()
    mock_default.return_value = (mock_creds, "proj")


@patch("src.vertex_client.requests.post")
@patch("google.auth.default")
def test_start_video_generation_success(mock_default, mock_post):
    setup_google_auth(mock_default)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"name": "operations/abc123"}
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp

    name = start_video_generation("hi", "proj", "us-central1", "mymodel", 6, 1)
    assert name == "operations/abc123"
    assert mock_post.called


@patch("src.vertex_client.requests.post")
@patch("google.auth.default")
def test_start_video_generation_http_error(mock_default, mock_post):
    setup_google_auth(mock_default)
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("boom")
    mock_post.return_value = mock_resp

    with pytest.raises(Exception):
        start_video_generation("hi", "proj", "us-central1", "mymodel", 6, 1)


@patch("src.vertex_client.requests.post")
@patch("google.auth.default")
def test_start_video_generation_missing_name(mock_default, mock_post):
    setup_google_auth(mock_default)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp

    with pytest.raises(RuntimeError):
        start_video_generation("hi", "proj", "us-central1", "mymodel", 6, 1)


@patch("src.vertex_client.requests.post")
@patch("google.auth.default")
def test_poll_video_generation_success(mock_default, mock_post):
    setup_google_auth(mock_default)

    running = MagicMock()
    running.json.return_value = {"done": False}
    running.raise_for_status.return_value = None

    done = MagicMock()
    done.json.return_value = {
        "done": True,
        "response": {"videos": [{"data": "aaa"}]},
    }
    done.raise_for_status.return_value = None

    mock_post.side_effect = [running, done]

    result = poll_video_generation(
        "projects/p/locations/us/operations/123",
        "us-central1",
        "proj",
        poll_interval=0,
    )

    assert result["done"] is True
    assert result["response"]["videos"][0]["data"] == "aaa"
    assert mock_post.call_count == 2


@patch("src.vertex_client.requests.post")
@patch("google.auth.default")
def test_poll_video_generation_http_error(mock_default, mock_post):
    setup_google_auth(mock_default)
    error_resp = MagicMock()
    error_resp.raise_for_status.side_effect = Exception("boom")
    mock_post.return_value = error_resp

    with pytest.raises(Exception):
        poll_video_generation(
            "projects/p/locations/us/operations/123",
            "us-central1",
            "proj",
            poll_interval=0,
        )


@patch("src.vertex_client.requests.post")
@patch("google.auth.default")
def test_poll_video_generation_missing_videos(mock_default, mock_post):
    setup_google_auth(mock_default)
    done = MagicMock()
    done.json.return_value = {"done": True, "response": {}}
    done.raise_for_status.return_value = None
    mock_post.return_value = done

    with pytest.raises(RuntimeError):
        poll_video_generation(
            "projects/p/locations/us/operations/123",
            "us-central1",
            "proj",
            poll_interval=0,
        )
