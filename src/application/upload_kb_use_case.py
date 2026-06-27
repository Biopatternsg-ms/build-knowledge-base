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
from src.infrastructure.storage.kb_storage_adapter import KbStorageAdapter

logger = logging.getLogger("build-knowledge-base.upload_kb_use_case")


class UploadKbUseCase:
    def __init__(self, storage: KbStorageAdapter):
        self.storage = storage

    def execute(self, pipeline_id: str, filename: str, data: bytes) -> dict:
        """
        Re-carga un archivo KB editado por el usuario a MinIO,
        reemplazando el archivo existente para ese pipeline.

        Args:
            pipeline_id: Identificador del pipeline.
            filename: Nombre del archivo a reemplazar (ej: 'kBase.pl').
            data: Contenido del nuevo archivo en bytes.

        Returns:
            Diccionario con el estado de la operación.
        """
        logger.info(
            f"Re-cargando archivo '{filename}' para pipeline={pipeline_id} "
            f"({len(data)} bytes)"
        )
        self.storage.upload(pipeline_id, filename, data)
        return {
            "status": "updated",
            "pipelineId": pipeline_id,
            "filename": filename,
            "sizeBytes": len(data)
        }
