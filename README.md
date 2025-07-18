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
