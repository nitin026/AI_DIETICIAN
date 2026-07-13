"""Endpoints for lab report biomarker extraction."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.services.report_parser import biomarker_status, extract_biomarkers_from_file, infer_conditions

router = APIRouter()

SUPPORTED_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/jpg"}


@router.post("/upload-report")
async def upload_report(file: UploadFile = File(...)) -> dict:
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_TYPES and not (file.filename or "").lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=415, detail="Upload a PDF, PNG, JPG, or JPEG lab report.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded report is empty.")

    biomarkers = await extract_biomarkers_from_file(content, file.filename or "report", content_type)
    biomarker_dict = biomarkers.model_dump()
    return {
        "filename": file.filename,
        "biomarkers": biomarker_dict,
        "statuses": {name: biomarker_status(name, value) for name, value in biomarker_dict.items()},
        "inferred_conditions": infer_conditions(biomarkers),
        "disclaimer": "Automated extraction can be wrong. Confirm values with the original report and a clinician.",
    }
