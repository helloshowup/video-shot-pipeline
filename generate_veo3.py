import base64
import logging
import time
from pathlib import Path
from typing import List

import google.auth
from google.auth.transport.requests import Request
import requests
from src.vertex_client import start_video_generation
import typer

app = typer.Typer(help="Bulk generate videos using Vertex AI Veo")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




def _get_token() -> tuple[str, str]:
    credentials, project_id = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(Request())
    return credentials.token, project_id


def _poll_operation(name: str, *, token: str, poll: int) -> dict:
    url = f"https://aiplatform.googleapis.com/v1/{name}"
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        resp = requests.get(url, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("done"):
            return data
        time.sleep(poll)


def _save_result(result: dict, outfile: Path) -> None:
    try:
        b64_data = result["response"]["predictions"][0]["bytes"]
    except KeyError:
        raise RuntimeError("Unexpected response format")
    binary = base64.b64decode(b64_data)
    outfile.write_bytes(binary)


@app.command()
def all(
    folder: Path,
    model: str = "veo-3.0-generate-preview",
    location: str = "us-central1",
    duration: int = 8,
    count: int = 1,
    poll: int = 5,
) -> None:
    """Generate videos for every .txt prompt in FOLDER."""
    token, project = _get_token()
    txt_files: List[Path] = sorted(folder.glob("*.txt"))
    if not txt_files:
        typer.echo("No prompt files found", err=True)
        raise typer.Exit(code=1)

    for prompt_file in txt_files:
        prompt = prompt_file.read_text().strip()
        if not prompt:
            logger.warning("Skipping %s: file is empty", prompt_file.name)
            continue
        typer.echo(f"Submitting {prompt_file.name}...")
        try:
            op_name = None
            for attempt in range(2):
                try:
                    op_name = start_video_generation(
                        prompt=prompt,
                        project=project,
                        location=location,
                        model=model,
                        duration=duration,
                        count=count,
                    )
                    break
                except Exception as exc:  # noqa: BLE001
                    logger.error("\u274c Failed to start job for %s: %s", prompt_file.stem, exc)
                    if attempt == 0:
                        time.sleep(2 ** (attempt + 1))
                    else:
                        raise

            typer.echo(f"Operation: {op_name}")
            result = _poll_operation(op_name, token=token, poll=poll)
            out_mp4 = prompt_file.with_suffix(".mp4")
            _save_result(result, out_mp4)
            typer.echo(f"Saved {out_mp4}")
        except Exception as e:  # noqa: BLE001
            typer.echo(f"Failed to process {prompt_file.name}: {e}", err=True)


if __name__ == "__main__":
    app()
