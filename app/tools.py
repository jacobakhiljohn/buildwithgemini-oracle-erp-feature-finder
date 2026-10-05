"""Firestore and utility tools for Oracle Cloud Fusion ERP Financials release features."""

import base64
import subprocess
import uuid
import requests
from google import genai
from google.genai import types
from google.adk.tools import ToolContext
from google.auth import default
from google.cloud import firestore, storage
from google.oauth2 import credentials

# CRITICAL: Hardcode project ID string and bucket name string (not project number)
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-ad74c104b331"
GCS_BUCKET_NAME = "oracle-erp-feature-assets-qwiklabs-gcp-01-ad74c104b331"


def get_firestore_client():
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        creds = credentials.Credentials(token)
        return firestore.Client(project=FIRESTORE_PROJECT_ID, credentials=creds)
    except Exception:
        creds, _ = default()
        return firestore.Client(project=FIRESTORE_PROJECT_ID, credentials=creds)


def search_erp_features(
    module: str = "",
    release_quarter: str = "",
    impact_level: str = "",
    query: str = "",
) -> list[dict]:
    """Search and filter Oracle Cloud Fusion ERP release features from Firestore.

    Args:
        module: Optional ERP module filter, e.g. "General Ledger", "Accounts Payable", "Accounts Receivable", "Fixed Assets", "Cash Management".
        release_quarter: Optional release quarter filter, e.g. "24A", "24B", "24C", "24D".
        impact_level: Optional impact level filter, e.g. "High", "Medium", "Low".
        query: Optional keyword query to match against feature name or summary.

    Returns:
        List of matching ERP feature dictionaries.
    """
    db = get_firestore_client()
    col = db.collection("erp_features")
    docs = col.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        if module and module.lower() not in data.get("module", "").lower():
            continue
        if (
            release_quarter
            and release_quarter.lower() != data.get("release_quarter", "").lower()
        ):
            continue
        if (
            impact_level
            and impact_level.lower() != data.get("impact_level", "").lower()
        ):
            continue
        if query:
            q_lower = query.lower()
            fname = data.get("feature_name", "").lower()
            summary = data.get("summary", "").lower()
            if q_lower not in fname and q_lower not in summary:
                continue
        results.append(data)

    return results


def add_erp_feature(
    feature_id: str,
    feature_name: str,
    module: str,
    release_quarter: str,
    summary: str,
    business_benefit: str,
    readiness_category: str = "Automatic",
    impact_level: str = "Medium",
) -> dict:
    """Add a new Oracle Cloud Fusion ERP release feature to Firestore.

    Args:
        feature_id: Unique feature identifier, e.g. "FEATURE-24D-GL-03".
        feature_name: Name of the feature update.
        module: Oracle ERP module, e.g. "General Ledger", "Accounts Payable".
        release_quarter: Release update quarter, e.g. "24D".
        summary: Clear summary of the feature functionality.
        business_benefit: Business or process benefit.
        readiness_category: "Automatic" or "Opt-In".
        impact_level: "High", "Medium", or "Low".

    Returns:
        Dictionary confirming the saved feature item.
    """
    db = get_firestore_client()
    item = {
        "feature_id": feature_id,
        "feature_name": feature_name,
        "module": module,
        "release_quarter": release_quarter,
        "summary": summary,
        "business_benefit": business_benefit,
        "readiness_category": readiness_category,
        "impact_level": impact_level,
    }
    db.collection("erp_features").document(feature_id).set(item)
    return {"status": "success", "feature": item}


def calculate_feature_roi_and_effort(
    module: str,
    impact_level: str = "Medium",
    monthly_transaction_volume: int = 1000,
    finance_team_size: int = 5,
) -> dict:
    """Calculates implementation effort (hours), testing requirements, and projected annual financial savings ($) for an Oracle ERP release feature.

    Args:
        module: Oracle ERP module, e.g. "General Ledger", "Accounts Payable", "Accounts Receivable", "Fixed Assets", "Cash Management".
        impact_level: Feature impact level ("High", "Medium", "Low").
        monthly_transaction_volume: Monthly transactions or journal entries processed in this module.
        finance_team_size: Number of finance analysts or users using this module.

    Returns:
        Dictionary with effort hours, testing hours, annual time saved, and projected annual savings ($).
    """
    impact_mult = {"high": 1.5, "medium": 1.0, "low": 0.6}.get(
        impact_level.lower(), 1.0
    )

    base_setup_hours = 12 * impact_mult
    testing_hours = 8 * impact_mult + (finance_team_size * 2)
    total_effort_hours = round(base_setup_hours + testing_hours, 1)

    hours_saved_per_month = (monthly_transaction_volume / 500) * impact_mult
    annual_hours_saved = round(hours_saved_per_month * 12, 1)
    projected_annual_savings_usd = round(annual_hours_saved * 75.0, 2)

    payback_months = (
        round(
            (total_effort_hours * 75.0) / (projected_annual_savings_usd / 12),
            1,
        )
        if projected_annual_savings_usd > 0
        else 0
    )

    return {
        "module": module,
        "impact_level": impact_level,
        "setup_effort_hours": round(base_setup_hours, 1),
        "testing_training_hours": round(testing_hours, 1),
        "total_effort_hours": total_effort_hours,
        "annual_hours_saved": annual_hours_saved,
        "projected_annual_savings_usd": projected_annual_savings_usd,
        "estimated_payback_period_months": payback_months,
    }


def get_foreign_exchange_rates(
    base_currency: str = "USD",
    target_currencies: str = "EUR,GBP,CAD,JPY,AUD",
) -> dict:
    """Fetch current foreign exchange rates from the European Central Bank (via Frankfurter API) for ERP multi-currency accounting and revaluation.

    Args:
        base_currency: Base ISO currency code (e.g., "USD", "EUR", "GBP").
        target_currencies: Comma-separated list of target ISO currency codes (e.g., "EUR,GBP,CAD,JPY,AUD").

    Returns:
        Dictionary containing base currency, date, and live conversion rates.
    """
    url = f"https://api.frankfurter.dev/v1/latest?base={base_currency.upper()}&symbols={target_currencies.upper()}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "error": f"Failed to fetch exchange rates: {str(e)}",
            "base": base_currency,
        }


async def generate_erp_feature_diagram(
    prompt: str,
    feature_id: str = "FEATURE-DIAGRAM",
    tool_context: ToolContext = None,
) -> dict:
    """Generates a visual process flow diagram for an Oracle ERP feature using gemini-3.1-flash-lite-image in the global region, saves it as an ADK artifact, and uploads it to public Cloud Storage.

    Args:
        prompt: Description of the ERP workflow process diagram to generate (e.g. "Automated General Ledger reconciliation process flow").
        feature_id: Optional feature identifier string.
        tool_context: ADK ToolContext for saving session artifacts.

    Returns:
        Dictionary containing the public Cloud Storage image URL and artifact details.
    """
    client = genai.Client(
        vertexai=True,
        project=FIRESTORE_PROJECT_ID,
        location="global",
    )

    full_prompt = (
        f"A clean, professional infographic diagram illustrating an Oracle Cloud ERP Financials workflow: {prompt}. "
        "Modern corporate design, high contrast, clear visual steps."
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=full_prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    image_bytes = None
    mime_type = "image/jpeg"
    for candidate in response.candidates:
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.inline_data:
                    image_bytes = part.inline_data.data
                    if part.inline_data.mime_type:
                        mime_type = part.inline_data.mime_type
                    break

    if not image_bytes:
        return {"error": "Failed to generate image bytes from model response."}

    ext = "png" if "png" in mime_type else "jpg"
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{feature_id.lower()}_{unique_id}.{ext}"

    # 1. Save artifact with tool_context.save_artifact for Playground Artifacts panel
    if tool_context:
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes directly to public GCS bucket
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        creds = credentials.Credentials(token)
        storage_client = storage.Client(
            project=FIRESTORE_PROJECT_ID, credentials=creds
        )
    except Exception:
        creds, _ = default()
        storage_client = storage.Client(
            project=FIRESTORE_PROJECT_ID, credentials=creds
        )

    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "feature_id": feature_id,
        "artifact_filename": filename,
        "public_image_url": public_url,
    }


async def generate_erp_feature_video(
    prompt: str,
    feature_id: str = "FEATURE-VIDEO",
    tool_context: ToolContext = None,
) -> dict:
    """Generates a short feature highlight video for an Oracle ERP Financials item using gemini-omni-flash-preview in the global region, saves it as an ADK artifact, and uploads it to public Cloud Storage.

    Args:
        prompt: Description of the ERP feature video to generate (e.g. "Short video highlight of automated AP invoice matching workflow").
        feature_id: Optional feature identifier string.
        tool_context: ADK ToolContext for saving session artifacts.

    Returns:
        Dictionary containing the public Cloud Storage video URL and artifact details.
    """
    client = genai.Client(
        vertexai=True,
        project=FIRESTORE_PROJECT_ID,
        location="global",
    )

    full_prompt = (
        f"A short video animation highlighting an Oracle Cloud Fusion ERP Financials release feature: {prompt}. "
        "Modern corporate design, high contrast, smooth animation."
    )

    interaction = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=full_prompt,
    )

    video_bytes = None
    mime_type = "video/mp4"

    if hasattr(interaction, "output_video") and interaction.output_video:
        out_vid = interaction.output_video
        if hasattr(out_vid, "data") and out_vid.data:
            if isinstance(out_vid.data, bytes):
                video_bytes = out_vid.data
            elif isinstance(out_vid.data, str):
                video_bytes = base64.b64decode(out_vid.data)
        elif hasattr(out_vid, "bytes") and out_vid.bytes:
            video_bytes = out_vid.bytes
        elif hasattr(out_vid, "uri") and out_vid.uri:
            resp = requests.get(out_vid.uri, timeout=30)
            if resp.status_code == 200:
                video_bytes = resp.content

    if not video_bytes:
        return {
            "error": "Failed to extract video bytes from gemini-omni-flash-preview response."
        }

    unique_id = uuid.uuid4().hex[:8]
    filename = f"{feature_id.lower()}_{unique_id}.mp4"

    # 1. Save artifact with tool_context.save_artifact for Playground Artifacts panel
    if tool_context:
        artifact_part = types.Part.from_bytes(
            data=video_bytes, mime_type=mime_type
        )
        await tool_context.save_artifact(
            filename=filename, artifact=artifact_part
        )

    # 2. Upload video bytes directly to public GCS bucket (no local file writing)
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        creds = credentials.Credentials(token)
        storage_client = storage.Client(
            project=FIRESTORE_PROJECT_ID, credentials=creds
        )
    except Exception:
        creds, _ = default()
        storage_client = storage.Client(
            project=FIRESTORE_PROJECT_ID, credentials=creds
        )

    bucket = storage_client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}"

    return {
        "status": "success",
        "feature_id": feature_id,
        "artifact_filename": filename,
        "public_video_url": public_url,
    }

