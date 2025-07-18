import google.auth
from google.auth.transport.requests import Request

# Load Application Default Credentials (ADC)
credentials, project_id = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

# Refresh the credentials to obtain a valid bearer token
credentials.refresh(Request())

print(f"Project ID: {project_id}")
print(f"Access Token: {credentials.token}")
print(f"Token Expiry: {credentials.expiry}")
