import logging
import time
from pathlib import Path
from typing import List

import google.auth
from src.vertex_client import (
    poll_video_generation,
    save_video,
    start_video_generation,
)
import typer

app = typer.Typer(help="Bulk generate videos using Vertex AI Veo")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




def _get_project() -> str:
    _, project_id = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return project_id




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
    project = _get_project()
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
            result = poll_video_generation(
                op_name,
                location=location,
                project=project,
                poll_interval=poll,
            )
            out_mp4 = prompt_file.with_suffix(".mp4")
            save_video(result["response"]["videos"][0], out_mp4)
            typer.echo(f"Saved {out_mp4}")
        except Exception as e:  # noqa: BLE001
            typer.echo(f"Failed to process {prompt_file.name}: {e}", err=True)


if __name__ == "__main__":
    app()
