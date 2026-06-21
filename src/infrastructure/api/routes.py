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
import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.application.get_hello_message import GetHelloMessageUseCase
from src.infrastructure.repositories.mock_hello_repository import MockHelloRepository

# Nuevas importaciones para el generador
from src.model.pubtator import PubTatorDocument
from src.application.generate_kb_use_case import GenerateKbUseCase
from src.infrastructure.generator.pubtator_kb_adapter import PubTatorKbAdapter

logger = logging.getLogger("build-knowledge-base.routes")
router = APIRouter()

class HelloResponse(BaseModel):
    message: str
    version: str
    status: str

# Esquema de respuesta para la generación de la KB
class GenerateKbResponse(BaseModel):
    status: str
    output_directory: str

def get_hello_use_case() -> GetHelloMessageUseCase:
    repository = MockHelloRepository()
    return GetHelloMessageUseCase(repository)

def get_generate_kb_use_case() -> GenerateKbUseCase:
    # Escribe las salidas en resources/output por defecto
    adapter = PubTatorKbAdapter(output_dir="resources/output", working_dir=".")
    return GenerateKbUseCase(adapter)

@router.get("/hello", response_model=HelloResponse)
def read_hello(use_case: GetHelloMessageUseCase = Depends(get_hello_use_case)):
    logger.info("Endpoint /hello fue consultado exitosamente a través de la arquitectura limpia")
    hello_msg = use_case.execute()
    return HelloResponse(
        message=hello_msg.message,
        version=hello_msg.version,
        status=hello_msg.status
    )

@router.post("/generate-kb", response_model=GenerateKbResponse)
def generate_kb(document: PubTatorDocument, use_case: GenerateKbUseCase = Depends(get_generate_kb_use_case)):
    logger.info(f"Petición POST /generate-kb recibida para PMID: {document.pmid}")
    output_dir = use_case.execute(document)
    return GenerateKbResponse(
        status="success",
        output_directory=output_dir
    )

