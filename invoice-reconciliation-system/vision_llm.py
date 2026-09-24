import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.8-flash")
MAX_RETRIES = 3


class GeminiUnavailableError(RuntimeError):
    """Raised when all configured Gemini models are temporarily unavailable."""


def _generate_with_retries(client: genai.Client, contents: list[object]) -> str:
    """Retry temporary capacity/rate-limit failures, then try the fallback model."""
    models = [MODEL_NAME]
    if FALLBACK_MODEL and FALLBACK_MODEL != MODEL_NAME:
        models.append(FALLBACK_MODEL)

    last_error: Exception | None = None
    for model in models:
        for attempt in range(MAX_RETRIES):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                )
                if not response.text:
                    raise RuntimeError(f"Gemini returned an empty response using {model}.")
                return response.text
            except Exception as error:
                last_error = error
                status_code = getattr(error, "status_code", None)
                error_text = str(error).upper()
                is_transient = status_code in {429, 500, 502, 503, 504}
                is_transient = is_transient or any(
                    marker in error_text for marker in ("429", "500", "502", "503", "504", "UNAVAILABLE")
                )
                if not is_transient:
                    raise
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2**attempt)

    raise GeminiUnavailableError(
        "Gemini models are temporarily unavailable. "
        "Please wait a moment and try again."
    ) from last_error


def analyze_documents(
    po_filename: str,
    po_bytes: bytes,
    gr_filename: str,
    gr_bytes: bytes,
    invoice_filename: str,
    invoice_bytes: bytes,
) -> str:
    """Sends the three PDFs directly to Gemini Vision using official SDK types."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from environment variables.")

    client = genai.Client(api_key=api_key)

    prompt = """
You are an expert invoice reconciliation assistant.

You are given three PDF documents:
1. Purchase Order (PO)
2. Goods Received Note (GRN)
3. Commercial Invoice

Perform a strict 3-way match across these three documents.

Compare:
- PO Number, GRN Number, and Invoice Number
- Vendor / Supplier Name
- Line-item details (Quantities ordered vs received vs billed)
- Unit Prices and Totals

Format your final response clearly using this exact structure:

STATUS: [MATCHED or NEEDS REVIEW]

SUMMARY OF DOCUMENTS:
- Purchase Order: [PO Number]
- Goods Received Note: [GRN Number]
- Invoice: [Invoice Number]
- Supplier Name: [Supplier]

DISCREPANCIES FOUND:
- [List each discrepancy clearly, e.g., line item quantity mismatches or price differences]
- [If no discrepancies exist, state "None"]

RECOMMENDED ACTION:
[Provide a 1-2 sentence recommendation for the finance team]
"""

    # Convert PDF byte buffers into official Gemini Parts
    po_part = types.Part.from_bytes(data=po_bytes, mime_type="application/pdf")
    gr_part = types.Part.from_bytes(data=gr_bytes, mime_type="application/pdf")
    invoice_part = types.Part.from_bytes(data=invoice_bytes, mime_type="application/pdf")

    contents = [
        prompt,
        f"\n--- DOCUMENT 1: Purchase Order ({po_filename}) ---",
        po_part,
        f"\n--- DOCUMENT 2: Goods Received Note ({gr_filename}) ---",
        gr_part,
        f"\n--- DOCUMENT 3: Commercial Invoice ({invoice_filename}) ---",
        invoice_part,
    ]

    return _generate_with_retries(client, contents)