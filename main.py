import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Build Knowledge Base Service",
    description="Servicio para construir bases de conocimiento y procesar pathways",
    version="1.0.0"
)

class PathwaysRequest(BaseModel):
    root_path: Optional[str] = None
    pathways: Optional[List[str]] = None

@app.get("/hello")
def read_hello():
    return {"message": "hello"}

