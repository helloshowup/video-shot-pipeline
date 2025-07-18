"""Vertex AI client utilities for Veo video generation."""

from __future__ import annotations

import base64
import time
from pathlib import Path
from typing import Any

import google.auth
from google.auth.transport.requests import Request
import requests


API_URL_TEMPLATE = (
    "https://{location}-aiplatform.googleapis.com/v1/"
    "projects/{project}/locations/{location}/publishers/"
    "google/models/{model}:predictLongRunning"
)


def start_video_generation(
    prompt: str,
    project: str,
    location: str,
    model: str,
    duration: int,
    count: int,
    generate_audio: bool = True,
) -> str:
    """Start a Veo predictLongRunning job.

    Parameters
    ----------
    prompt:
        Text prompt to generate from.
    project:
        GCP project ID for the request.
    location:
        Region for the API endpoint.
    model:
        Vertex model ID.
    duration:
        Duration of the resulting video in seconds.
    count:
        Number of samples to generate.
    generate_audio:
        Whether to generate audio with the video.

    Returns
    -------
    str
        The operation name from the API response.

    Raises
    ------
    requests.HTTPError
        If the HTTP request returned an unsuccessful status.
    RuntimeError
        If the response does not contain an operation name.
    """

    url = API_URL_TEMPLATE.format(project=project, location=location, model=model)

    body: dict[str, Any] = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": count,
            "videoConfig": {
                "duration": f"{duration}s",
                "generateAudio": generate_audio,
            },
        },
    }

    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(Request())
    headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}

    resp = requests.post(url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "name" not in data:
        raise RuntimeError("Missing operation name in response")
    return data["name"]


def poll_video_generation(
    operation_name: str,
    location: str,
    project: str,
    poll_interval: int = 5,
) -> dict:
    """Poll the Veo 3 long-running operation until completion.

    Parameters
    ----------
    operation_name:
        Name of the long-running operation returned by ``start_video_generation``.
    location:
        Region for the API endpoint.
    project:
        Google Cloud project ID.
    poll_interval:
        Seconds to wait between polls.

    Returns
    -------
    dict
        Full JSON response from the ``fetchPredictOperation`` endpoint.

    Raises
    ------
    requests.HTTPError
        If the HTTP request returned an unsuccessful status.
    TimeoutError
        If the operation does not complete within two minutes.
    RuntimeError
        If the operation completes but lacks a video payload.
    """

    fetch_url = (
        f"https://{location}-aiplatform.googleapis.com/v1/{operation_name}:"
        "fetchPredictOperation"
    )

    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(Request())
    headers = {"Authorization": f"Bearer {creds.token}"}

    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        resp = requests.post(fetch_url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("done"):
            if not (data.get("response") and data["response"].get("videos")):
                raise RuntimeError("Operation completed without video payload")
            return data
        time.sleep(poll_interval)

    raise TimeoutError("Polling timed out after 120 seconds")


def save_video(video_payload: dict, output_path: Path) -> None:
    """Decode a base64 video payload and write it to ``output_path``.

    The function looks for ``bytesBase64Encoded`` or ``data`` fields in
    ``video_payload``.  The decoded bytes are written as binary.

    Parameters
    ----------
    video_payload:
        Individual video dictionary from the API response.
    output_path:
        Where to write the resulting MP4 file.

    Raises
    ------
    KeyError
        If no base64 field is present in ``video_payload``.
    """

    b64 = video_payload.get("bytesBase64Encoded") or video_payload.get("data")
    if b64 is None:
        raise KeyError("Video payload missing base64 data")

    binary = base64.b64decode(b64)
    output_path.write_bytes(binary)
