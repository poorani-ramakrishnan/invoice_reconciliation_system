import requests
import streamlit as st

API_URL = "http://127.0.0.1:8001/process-invoice/"
FASTAPI_URL = "http://127.0.0.1:8001/process-invoice/"

st.set_page_config(page_title="Invoice Reconciliation")

st.title("Invoice Reconciliation System")
st.write("Upload the PO, Goods Received Note, and Invoice as PDF files.")

purchase_order = st.file_uploader(
    "Upload Purchase Order",
    type=["pdf"],
)

goods_receipt = st.file_uploader(
    "Upload Goods Received Note",
    type=["pdf"],
)

invoice = st.file_uploader(
    "Upload Invoice",
    type=["pdf"],
)


if st.button("Run Three-Way Match"):
    if not purchase_order or not goods_receipt or not invoice:
        st.warning("Please upload all three PDF files.")

    else:
        files = {
            "po_file": (
                purchase_order.name,
                purchase_order.getvalue(),
                "application/pdf",
            ),
            "gr_file": (
                goods_receipt.name,
                goods_receipt.getvalue(),
                "application/pdf",
            ),
            "invoice_file": (
                invoice.name,
                invoice.getvalue(),
                "application/pdf",
            ),
        }

        try:
            with st.spinner("Gemini is reading the documents..."):
                response = requests.post(
                    API_URL,
                    files=files,
                    timeout=180,
                )

            response.raise_for_status()

            data = response.json()

            st.success("Reconciliation completed.")
            st.subheader("Result")
            st.write(data["result"])

        except requests.RequestException as error:
            st.error(f"Could not connect to FastAPI: {error}")