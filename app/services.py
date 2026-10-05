"""Custom service configuration for ADK.

Sets default environment variables so ADK auto-configures VertexAiMemoryBankService
in deployed container runtimes where CLI flags/deployment env vars are restricted.
"""

import os

os.environ.setdefault("GOOGLE_CLOUD_AGENT_ENGINE_ID", "6044834554047365120")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-01-ad74c104b331")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-east1")
