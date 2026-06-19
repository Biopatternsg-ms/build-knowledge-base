import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Configuración básica del sistema de logs de Python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("build-knowledge-base")

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
    logger.info("Endpoint /hello fue consultado exitosamente")
    return {"message": "hello"}

