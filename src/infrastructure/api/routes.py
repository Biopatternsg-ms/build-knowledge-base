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
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

from src.application.get_hello_message import GetHelloMessageUseCase
from src.infrastructure.repositories.mock_hello_repository import MockHelloRepository

from src.model.pubtator import PubTatorDocument
from src.application.generate_kb_use_case import GenerateKbUseCase
from src.application.download_kb_use_case import DownloadKbUseCase
from src.application.upload_kb_use_case import UploadKbUseCase
from src.infrastructure.generator.pubtator_kb_adapter import PubTatorKbAdapter
from src.infrastructure.storage.kb_storage_adapter import KbStorageAdapter

logger = logging.getLogger("build-knowledge-base.routes")
router = APIRouter()

# Archivos KB válidos para descarga/carga
VALID_KB_FILES = {"kBase.pl", "kBaseDoc.txt", "synonyms.pl", "aligned.pl", "biotypes.pl"}


# ---------------------------------------------------------------------------
# Schemas de respuesta
# ---------------------------------------------------------------------------

class HelloResponse(BaseModel):
    message: str
    version: str
    status: str


class KbRelation(BaseModel):
    """Componentes estructurados de un evento de la base de conocimiento."""
    first: str
    relation: str
    second: str


class KbEventResponse(BaseModel):
    """Un evento de la base de conocimiento con sus PubMed IDs asociados."""
    event: KbRelation
    pubmedIds: List[str]



class AlignedResponse(BaseModel):
    """Estructura equivalente al contenido de aligned.pl."""
    aligned: List[str]
    no_aligned: List[str]
    aligned_as: List[List[str]]
    aligned_objs: Dict[str, Any]
    no_aligned_objs: Dict[str, Any]


class GenerateKbResponse(BaseModel):
    """Respuesta completa del endpoint POST /generate-kb."""
    pipelineId: str
    pmid: str
    events: List[KbEventResponse]
    synonyms: Dict[str, List[str]]
    aligned: AlignedResponse
    biotypes: Dict[str, str]


class UploadKbResponse(BaseModel):
    status: str
    pipelineId: str
    filename: str
    sizeBytes: int


# ---------------------------------------------------------------------------
# Dependency providers
# ---------------------------------------------------------------------------

def get_hello_use_case() -> GetHelloMessageUseCase:
    repository = MockHelloRepository()
    return GetHelloMessageUseCase(repository)

def get_storage_adapter() -> KbStorageAdapter:
    return KbStorageAdapter()

def get_generate_kb_use_case() -> GenerateKbUseCase:
    adapter = PubTatorKbAdapter(output_dir="resources/output", working_dir=".")
    return GenerateKbUseCase(adapter)

def get_download_kb_use_case(
    storage: KbStorageAdapter = Depends(get_storage_adapter)
) -> DownloadKbUseCase:
    return DownloadKbUseCase(storage)

def get_upload_kb_use_case(
    storage: KbStorageAdapter = Depends(get_storage_adapter)
) -> UploadKbUseCase:
    return UploadKbUseCase(storage)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

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
def generate_kb(
    document: PubTatorDocument,
    use_case: GenerateKbUseCase = Depends(get_generate_kb_use_case)
):
    """
    Genera la base de conocimiento a partir de un documento PubTator y retorna
    toda la información estructurada como JSON.

    El campo `pipelineId` es obligatorio. Cada llamada es independiente:
    no se acumula estado en almacenamiento externo.

    La respuesta incluye:
    - **events**: lista de eventos `event('S',rel,'O')` con sus PubMed IDs asociados.
    - **synonyms**: sinónimos de cada objeto presente en la KB.
    - **aligned**: estructura de alineación de objetos del usuario.
    - **biotypes**: tipo biológico de cada objeto (protein, ligand, disease, ...).
    """
    logger.info(f"POST /generate-kb — pmid={document.pmid}, pipelineId={document.pipelineId}")
    result = use_case.execute(document)
    return GenerateKbResponse(
        pipelineId=result["pipelineId"],
        pmid=result["pmid"],
        events=[KbEventResponse(**e) for e in result["events"]],
        synonyms=result["synonyms"],
        aligned=AlignedResponse(**result["aligned"]),
        biotypes=result["biotypes"],
    )


@router.get(
    "/pipeline/{pipeline_id}/kb/{filename}",
    deprecated=True,
)
def download_kb_file(
    pipeline_id: str,
    filename: str,
    use_case: DownloadKbUseCase = Depends(get_download_kb_use_case)
):
    """
    **[DEPRECATED]** Descarga un archivo KB desde MinIO para el pipeline indicado.

    Este endpoint ya no tiene datos que servir: el endpoint `POST /generate-kb`
    ahora retorna la información directamente en la respuesta JSON y no persiste
    archivos en MinIO. Este endpoint se mantiene por compatibilidad con integraciones
    existentes, pero será eliminado en una versión futura.

    Archivos válidos: kBase.pl, kBaseDoc.txt, synonyms.pl, aligned.pl, biotypes.pl
    """
    if filename not in VALID_KB_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo '{filename}' no es un archivo KB válido. "
                   f"Archivos válidos: {sorted(VALID_KB_FILES)}"
        )

    # biotypes.pl se almacena bajo el subdirectorio biotypes/
    storage_filename = f"biotypes/{filename}" if filename == "biotypes.pl" else filename

    logger.info(f"GET /pipeline/{pipeline_id}/kb/{filename} [DEPRECATED]")
    data = use_case.execute(pipeline_id, storage_filename)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail=f"Archivo '{filename}' no encontrado para el pipeline '{pipeline_id}'. "
                   "Es posible que el pipeline aún no haya sido procesado."
        )

    return StreamingResponse(
        content=io.BytesIO(data),
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(data))
        }
    )


@router.put(
    "/pipeline/{pipeline_id}/kb/{filename}",
    response_model=UploadKbResponse,
    deprecated=True,
)
async def upload_kb_file(
    pipeline_id: str,
    filename: str,
    file: UploadFile = File(...),
    use_case: UploadKbUseCase = Depends(get_upload_kb_use_case)
):
    """
    **[DEPRECATED]** Re-carga un archivo KB editado por el usuario para el pipeline indicado.
    Reemplaza completamente el archivo existente en MinIO.

    Este endpoint ya no es necesario: el endpoint `POST /generate-kb` ahora retorna
    la información directamente en la respuesta JSON sin persistir en MinIO. Este
    endpoint se mantiene por compatibilidad, pero será eliminado en una versión futura.

    Archivos válidos: kBase.pl, kBaseDoc.txt, synonyms.pl, aligned.pl, biotypes.pl
    """
    if filename not in VALID_KB_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo '{filename}' no es un archivo KB válido. "
                   f"Archivos válidos: {sorted(VALID_KB_FILES)}"
        )

    # biotypes.pl se almacena bajo el subdirectorio biotypes/
    storage_filename = f"biotypes/{filename}" if filename == "biotypes.pl" else filename

    logger.info(f"PUT /pipeline/{pipeline_id}/kb/{filename} [DEPRECATED] — archivo recibido: {file.filename}")
    data = await file.read()
    result = use_case.execute(pipeline_id, storage_filename, data)

    return UploadKbResponse(**result)
