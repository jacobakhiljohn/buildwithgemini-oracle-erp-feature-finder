# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    add_erp_feature,
    calculate_feature_roi_and_effort,
    generate_erp_feature_diagram,
    generate_erp_feature_video,
    get_foreign_exchange_rates,
    search_erp_features,
)

# Read agent engine resource name from deployment_metadata.json
metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
AGENT_ENGINE_RESOURCE_NAME = (
    "projects/37354976717/locations/us-east1/reasoningEngines/6044834554047365120"
)
if metadata_path.exists():
    try:
        meta_data = json.loads(metadata_path.read_text())
        AGENT_ENGINE_RESOURCE_NAME = meta_data.get(
            "remote_agent_runtime_id", AGENT_ENGINE_RESOURCE_NAME
        )
    except Exception:
        pass

MEMORY_BANK_ID = AGENT_ENGINE_RESOURCE_NAME.split("/")[-1]
GCP_PROJECT_ID = "qwiklabs-gcp-01-ad74c104b331"
GCP_LOCATION = "us-east1"

# Memory service instance for future redeploys
memory_service = VertexAiMemoryBankService(
    project=GCP_PROJECT_ID,
    location=GCP_LOCATION,
    agent_engine_id=MEMORY_BANK_ID,
)

sandbox_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME
)


async def generate_memories_callback(callback_context: CallbackContext):
    """WRITE: after each turn, send the session to Memory Bank for extraction."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        sess = getattr(getattr(callback_context, "_invocation_context", None), "session", None)
        if sess is not None:
            try:
                await memory_service.add_session_to_memory(sess)
            except Exception as e:
                print(f"Memory save fallback error: {e}")
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are an expert Oracle Cloud Fusion ERP Financials assistant. "
        "Help users search, analyze, and summarize current year (2025/2026: 25A-25D, 26A-26C) and historical quarterly release features "
        "(e.g., General Ledger, Accounts Payable, Accounts Receivable, Fixed Assets, Cash Management), "
        "calculate implementation ROI, fetch live FX exchange rates, generate process flow diagrams, "
        "and generate short feature video highlights using your tools "
        "(`search_erp_features`, `add_erp_feature`, `calculate_feature_roi_and_effort`, "
        "`get_foreign_exchange_rates`, `generate_erp_feature_diagram`, `generate_erp_feature_video`). "
        "If a new 2026 feature is not yet in the database, you can also use `add_erp_feature` to store it. "
        "You remember user preferences and facts across sessions using Memory Bank, specifically tracking "
        "and prioritizing the user's most frequent ERP domains (such as Financials, Procurement, Supply Chain, "
        "HCM, or Projects) to personalize future search recommendations and feature analyses. "
        "You can also safely execute Python code calculations using your Agent Platform sandbox code executor."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        search_erp_features,
        add_erp_feature,
        calculate_feature_roi_and_effort,
        get_foreign_exchange_rates,
        generate_erp_feature_diagram,
        generate_erp_feature_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
    code_executor=sandbox_executor,
)

app = App(
    root_agent=root_agent,
    name="app",
)
