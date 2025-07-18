"""Vertex AI client utilities for Veo video generation."""

from __future__ import annotations

import json
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
