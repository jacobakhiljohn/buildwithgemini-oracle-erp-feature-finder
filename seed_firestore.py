"""Seed script for Oracle Cloud Fusion ERP Financials release features in Firestore."""

import subprocess
from google.auth import default
from google.cloud import firestore
from google.oauth2 import credentials

# CRITICAL: Hardcode project ID string (not project number)
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-ad74c104b331"

SEED_FEATURES = [
    # 2026 Release Features
    {
        "feature_id": "FEATURE-26C-GL-01",
        "feature_name": "Generative AI Financial Narrative & Variance Explanation",
        "module": "General Ledger",
        "release_quarter": "26C",
        "summary": "Generates natural language executive commentaries for balance sheet and P&L variances during financial close.",
        "business_benefit": "Reduces manual management reporting preparation from days to minutes.",
        "readiness_category": "Opt-In",
        "impact_level": "High",
    },
    {
        "feature_id": "FEATURE-26B-AP-01",
        "feature_name": "Autonomous e-Invoice Audit & ESG Tax Compliance",
        "module": "Accounts Payable",
        "release_quarter": "26B",
        "summary": "Automates global e-invoicing audit trails with real-time tax jurisdiction validation and Scope 3 carbon tracking.",
        "business_benefit": "Ensures global e-invoicing tax compliance and automated ESG carbon footprint reporting.",
        "readiness_category": "Automatic",
        "impact_level": "High",
    },
    {
        "feature_id": "FEATURE-26A-CM-01",
        "feature_name": "ISO 20022 Instant Payment & Liquidity Optimization",
        "module": "Cash Management",
        "release_quarter": "26A",
        "summary": "Real-time cross-border instant settlement routing using ISO 20022 messaging and predictive cash balance pooling.",
        "business_benefit": "Maximizes yield on excess intraday balances and slashes cross-border wire fees.",
        "readiness_category": "Opt-In",
        "impact_level": "Medium",
    },
    # 2025 Release Features
    {
        "feature_id": "FEATURE-25D-AR-01",
        "feature_name": "AI Dispute Resolution & Automated Dunning Assistant",
        "module": "Accounts Receivable",
        "release_quarter": "25D",
        "summary": "Intelligent agent that handles customer short-pay inquiries, validates claim backup documents, and adjusts billing holds.",
        "business_benefit": "Drives a 25% reduction in Days Sales Outstanding (DSO) and shortens dispute resolution turnaround.",
        "readiness_category": "Opt-In",
        "impact_level": "High",
    },
    {
        "feature_id": "FEATURE-25C-FA-01",
        "feature_name": "Automated ESG Carbon Asset Depreciation",
        "module": "Fixed Assets",
        "release_quarter": "25C",
        "summary": "Tracks carbon credit capital assets and automates regulatory impairment testing for green energy investments.",
        "business_benefit": "Ensures compliance with global SEC and EU ESG asset accounting mandates.",
        "readiness_category": "Automatic",
        "impact_level": "Medium",
    },
    # 2024 Release Features
    {
        "feature_id": "FEATURE-24C-GL-01",
        "feature_name": "Automated Journal Entry Reconciliation with AI",
        "module": "General Ledger",
        "release_quarter": "24C",
        "summary": "Uses AI matching algorithms to automatically reconcile complex intercompany and general ledger journal entries.",
        "business_benefit": "Reduces period-end close cycle time by up to 40% and minimizes manual reconciliation errors.",
        "readiness_category": "Automatic",
        "impact_level": "High",
    },
    {
        "feature_id": "FEATURE-24C-AP-02",
        "feature_name": "Smart Supplier Invoice Line Matching",
        "module": "Accounts Payable",
        "release_quarter": "24C",
        "summary": "Enhances 2-way and 3-way matching for multi-line supplier invoices with automated tax line item distribution.",
        "business_benefit": "Accelerates accounts payable processing and prevents duplicate payment holds.",
        "readiness_category": "Opt-In",
        "impact_level": "High",
    },
    {
        "feature_id": "FEATURE-24D-AR-01",
        "feature_name": "Predictive Cash Collections Insights",
        "module": "Accounts Receivable",
        "release_quarter": "24D",
        "summary": "Provides machine-learning driven customer payment predictions and automated dunning letter triggers.",
        "business_benefit": "Improves Days Sales Outstanding (DSO) and prioritizes high-risk collection accounts.",
        "readiness_category": "Opt-In",
        "impact_level": "Medium",
    },
    {
        "feature_id": "FEATURE-24D-FA-01",
        "feature_name": "Lease Accounting IFRS 16 Automated Adjustments",
        "module": "Fixed Assets",
        "release_quarter": "24D",
        "summary": "Automates Right-of-Use asset amortization and interest liability recalculations upon lease modification.",
        "business_benefit": "Ensures continuous IFRS 16 compliance and streamlines lease schedule audits.",
        "readiness_category": "Automatic",
        "impact_level": "Medium",
    },
    {
        "feature_id": "FEATURE-24B-CM-01",
        "feature_name": "Real-Time Bank Statement API Integration",
        "module": "Cash Management",
        "release_quarter": "24B",
        "summary": "Direct REST API connection with major global banks for intraday bank statement ingestion and cash positioning.",
        "business_benefit": "Eliminates manual BAI2/SWIFT file uploads and enables real-time liquidity visibility.",
        "readiness_category": "Opt-In",
        "impact_level": "High",
    },
]


def get_db():
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-access-token"], text=True
        ).strip()
        creds = credentials.Credentials(token)
        return firestore.Client(project=FIRESTORE_PROJECT_ID, credentials=creds)
    except Exception:
        creds, _ = default()
        return firestore.Client(project=FIRESTORE_PROJECT_ID, credentials=creds)


def seed():
    print(f"Connecting to Firestore for project '{FIRESTORE_PROJECT_ID}'...")
    db = get_db()
    collection_ref = db.collection("erp_features")

    for item in SEED_FEATURES:
        doc_id = item["feature_id"]
        collection_ref.document(doc_id).set(item)
        print(f"  [+] Seeded feature: {doc_id} - {item['feature_name']}")

    print("Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed()
