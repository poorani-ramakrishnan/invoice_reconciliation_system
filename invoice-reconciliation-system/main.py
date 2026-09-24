import traceback
from fastapi import FastAPI, File, HTTPException, UploadFile
from google.genai.errors import APIError
from vision_llm import GeminiUnavailableError, analyze_documents

app = FastAPI(title="Invoice Reconciliation API")


@app.get("/")
def home():
    return {"status": "FastAPI is running!"}


@app.post("/process-invoice/")
@app.post("/process-invoice")
async def process_invoice(
    po_file: UploadFile = File(...),
    gr_file: UploadFile = File(...),
    invoice_file: UploadFile = File(...),
):
    try:
        po_bytes = await po_file.read()
        gr_bytes = await gr_file.read()
        invoice_bytes = await invoice_file.read()

        result = analyze_documents(
            po_file.filename,
            po_bytes,
            gr_file.filename,
            gr_bytes,
            invoice_file.filename,
            invoice_bytes,
        )

        return {
            "status": "success",
            "result": result,
        }

    except GeminiUnavailableError as error:
        print("\n--- GEMINI TEMPORARILY UNAVAILABLE ---")
        traceback.print_exc()
        print("--------------------------------------\n")
        raise HTTPException(status_code=503, detail=str(error)) from error

    except APIError as error:
        print("\n--- GEMINI API ERROR ---")
        traceback.print_exc()
        print("------------------------\n")
        status_code = getattr(error, "status_code", 502)
        if status_code in {429, 500, 502, 503, 504}:
            status_code = 503
        else:
            status_code = 502
        raise HTTPException(status_code=status_code, detail=str(error)) from error

    except Exception as error:
        print("\n--- ERROR OCCURRED ---")
        traceback.print_exc()
        print("----------------------\n")

        raise HTTPException(status_code=500, detail=f"{type(error).__name__}: {str(error)}") from error