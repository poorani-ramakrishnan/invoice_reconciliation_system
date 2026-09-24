import traceback
from fastapi import FastAPI, File, HTTPException, UploadFile
from vision_llm import analyze_documents

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

    except Exception as error:
        print("\n--- ERROR OCCURRED ---")
        traceback.print_exc()
        print("----------------------\n")

        raise HTTPException(
            status_code=500, detail=f"{type(error).__name__}: {str(error)}"
        )