#
# Copyright © 2026 biopatternsg (biopatternsg@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.infrastructure.api.routes import router as api_router

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

app.include_router(api_router)

class PathwaysRequest(BaseModel):
    root_path: Optional[str] = None
    pathways: Optional[List[str]] = None
