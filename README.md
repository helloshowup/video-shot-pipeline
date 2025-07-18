# **Python CLI for Bulk Video Generation with Vertex AI Veo**

A minimalist Python CLI for bulk-generating MP4s from text files using Google Vertex AI Veo. Point it at a folder of `*.txt` prompts, and it will:

1. Kick off a `predictLongRunning` job for each prompt.
2. Poll the operation until it’s complete.
3. Decode the base64 video payload.
4. Save each result as `{promptName}.mp4`.

## **Key Points**

* **Zero-config aside from ADC:** Just run `gcloud auth application-default login` and set your project.
* **Batch-oriented:** Processes every text file in a directory in one go.
* **Resilient:** Logs failures per file and continues with the rest of the batch.
* **Extensible:** Designed to be easily modified. You can swap in GCS for output, or tweak parameters like duration, region, and model via CLI flags.

## **Requirements**

* Python 3.8+
* `gcloud` CLI with Application Default Credentials (ADC) enabled.
* The Python libraries listed in `requirements.txt`.

## Quick Start

```bash
pip install -r requirements.txt
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
python generate_veo3.py all ./prompts --duration 6 --count 2
```

## Environment & Authentication

Configure Application Default Credentials (ADC) with the `gcloud` CLI:

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

After configuration you can verify the credentials and fetch a bearer token by running the helper script:

```bash
python adc_token.py
```

## Running the CLI

Use `generate_veo3.py` to process every `*.txt` file in a folder:

```bash
python generate_veo3.py all ./prompts --duration 6 --count 2
```

CLI options:

* `folder` – path to the prompt files.
* `--model` – Vertex model ID (default `veo-3.0-generate-preview`).
* `--location` – region for the request (default `us-central1`).
* `--duration` – video duration in seconds (default `8`).
* `--count` – number of samples to generate (default `1`).
* `--poll` – polling interval in seconds (default `5`).

## Client module

`src/vertex_client.py` provides a lightweight helper for starting Veo jobs. You
can swap in your own publisher or model by editing the URL template, or use a
`storageUri` parameter to write results to a private bucket instead of returning
base64 bytes.

### Polling & Saving

The CLI now delegates polling and saving to `poll_video_generation` and
`save_video`. Adjust how often the status is checked with the `--poll` option
(seconds). Results are written next to your prompt files using the prompt's stem
as the filename.

`poll_video_generation` raises a `TimeoutError` after roughly two minutes if the
operation has not completed, and a `RuntimeError` if the operation finishes but
no video payload is returned.

## JSON schema

```json
"parameters": {
  "durationSeconds": <int>,
  "sampleCount": <int>,
  "generateAudio": true,
  "storageUri": <optional-gs-uri>
}
```
