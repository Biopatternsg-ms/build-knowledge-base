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

logger = logging.getLogger("build-knowledge-base.generate_kb_use_case")


class GenerateKbUseCase:
    def __init__(self, adapter: PubTatorKbAdapter):
        self.adapter = adapter

    def execute(self, document: PubTatorDocument) -> dict:
        """
        Genera la base de conocimiento para el documento recibido y retorna
        toda la información estructurada como un diccionario JSON-serializable.

        Cada llamada es independiente: no se acumula estado en MinIO ni en
        ningún almacenamiento externo.

        Returns:
            Diccionario con:
              - pipelineId: str
              - pmid:       str
              - events:     list[{event, pubmedIds}]
              - synonyms:   dict[str, list[str]]
              - aligned:    dict (estructura equivalente a aligned.pl)
              - biotypes:   dict[str, str]
        """
        pipeline_id = document.pipelineId
        logger.info(f"Generando KB — pipeline={pipeline_id}, pmid={document.pmid}")

        kb_data = self.adapter.generate_kb_as_json(document)

        return {
            "pipelineId": pipeline_id,
            "pmid":       document.pmid,
            **kb_data,
        }
