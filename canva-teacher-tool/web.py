"""
Canva Teacher Tool - Web API wrapper for Railway.app deployment.

Endpoints:
  POST /generate       Generate teacher documents (returns PNG bytes or base64)
  GET  /health         Health check for Railway
  GET  /output/{file}  Download generated file

The underlying generators come from main.py and use Playwright + Pillow.
"""

import sys
import base64
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Make parent module imports available
sys.path.insert(0, str(Path(__file__).parent))
from main import (
    SchoolDatabase,
    TEACHING_POSITIONS,
    generate_employment_letter,
    generate_teacher_id,
    generate_teaching_license,
    OUTPUT_DIR,
)

BASE_DIR = Path(__file__).parent
app = FastAPI(title="Canva Teacher Document Generator")
schools = SchoolDatabase()

# Ensure output directory exists before static mount
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Serve generated files
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# Serve the frontend UI
@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = BASE_DIR / "templates" / "index.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


class GenerateRequest(BaseModel):
    doc_type: str = "all"  # employment_letter | teacher_id | teaching_license | all
    name: Optional[str] = None
    school: Optional[str] = None
    position: Optional[str] = None
    format: str = "bytes"  # bytes | base64 | json


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/schools")
async def list_schools():
    return {"schools": schools.list_names()}


@app.post("/generate")
async def generate(req: GenerateRequest):
    doc_type = req.doc_type
    if doc_type not in {"employment_letter", "teacher_id", "teaching_license", "all"}:
        raise HTTPException(status_code=400, detail="invalid doc_type")

    # Parse/generate identity
    if req.name:
        parts = req.name.split()
        first, last = parts[0], parts[-1] if len(parts) > 1 else parts[0]
    else:
        from main import generate_name
        first, last = generate_name()

    if req.school:
        school = schools.search(req.school)
        if not school:
            raise HTTPException(status_code=404, detail=f"school '{req.school}' not found")
    else:
        school = schools.random()

    position = req.position or __import__("random").choice(TEACHING_POSITIONS)

    from main import generate_dob
    dob = generate_dob()

    OUTPUT_DIR.mkdir(exist_ok=True)

    doc_types = (
        ["employment_letter", "teacher_id", "teaching_license"]
        if doc_type == "all"
        else [doc_type]
    )

    results = []
    for dt in doc_types:
        try:
            if dt == "employment_letter":
                data = await generate_employment_letter(first, last, school, position)
            elif dt == "teacher_id":
                data = await generate_teacher_id(first, last, school, position, dob)
            else:
                data = await generate_teaching_license(first, last)

            filename = f"{dt}_{first}_{last}.png"
            path = OUTPUT_DIR / filename
            path.write_bytes(data)

            results.append(
                {
                    "doc_type": dt,
                    "filename": filename,
                    "size": len(data),
                    "download_url": f"/output/{filename}",
                }
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{dt} failed: {e}")

    # If single doc requested and format=bytes, return raw PNG
    if len(results) == 1 and req.format == "bytes":
        path = OUTPUT_DIR / results[0]["filename"]
        return Response(content=path.read_bytes(), media_type="image/png")

    # If format=base64, embed data
    if req.format == "base64":
        for r in results:
            r["base64"] = base64.b64encode(
                (OUTPUT_DIR / r["filename"]).read_bytes()
            ).decode("utf-8")

    return JSONResponse(
        content={
            "teacher": f"{first} {last}",
            "school": school["name"],
            "position": position,
            "dob": dob,
            "documents": results,
        }
    )


@app.get("/output/{filename}")
async def download(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path, media_type="image/png", filename=filename)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(__import__("os").getenv("PORT", "8080")))
