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
from src.model.pubtator import PubTatorDocument
from src.infrastructure.generator.pubtator_kb_adapter import PubTatorKbAdapter
from src.infrastructure.storage.kb_storage_adapter import KbStorageAdapter

logger = logging.getLogger("build-knowledge-base.generate_kb_use_case")

# Archivos KB gestionados en MinIO
KB_FILES = ["kBase.pl", "kBaseDoc.txt", "synonyms.pl", "aligned.pl", "biotypes/biotypes.pl"]


class GenerateKbUseCase:
    def __init__(self, adapter: PubTatorKbAdapter, storage: KbStorageAdapter):
        self.adapter = adapter
        self.storage = storage

    def execute(self, document: PubTatorDocument) -> dict:

        pipeline_id = document.pipelineId
        logger.info(f"Generando KB acumulativo — pipeline={pipeline_id}, pmid={document.pmid}")

        # 1. Descargar acumulado existente de MinIO
        existing_bytes = {}
        for filename in KB_FILES:
            data = self.storage.download(pipeline_id, filename)
            if data is not None:
                existing_bytes[filename] = data

        # 2. Generar o mergear según si ya hay acumulado
        if not existing_bytes:
            logger.info(f"Pipeline {pipeline_id}: primer documento — generando KB inicial")
            new_kb_bytes = self.adapter.generate_kb_to_bytes(document)
        else:
            logger.info(f"Pipeline {pipeline_id}: mergeando con KB acumulado existente")
            new_kb_bytes = self.adapter.merge_kb_bytes(existing_bytes, document)

        # 3. Subir archivos actualizados a MinIO
        uploaded_keys = []
        for filename, data in new_kb_bytes.items():
            self.storage.upload(pipeline_id, filename, data)
            uploaded_keys.append(f"pipelines/{pipeline_id}/{filename}")

        logger.info(f"Pipeline {pipeline_id}: {len(uploaded_keys)} archivos subidos a MinIO")

        return {
            "pipelineId": pipeline_id,
            "pmid": document.pmid,
            "files": uploaded_keys
        }
