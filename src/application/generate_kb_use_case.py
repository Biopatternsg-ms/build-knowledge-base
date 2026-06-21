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
from src.model.pubtator import PubTatorDocument
from src.infrastructure.generator.pubtator_kb_adapter import PubTatorKbAdapter

class GenerateKbUseCase:
    def __init__(self, adapter: PubTatorKbAdapter):
        self.adapter = adapter

    def execute(self, document: PubTatorDocument) -> str:
        """Ejecuta la generación de la Base de Conocimiento a partir de un JSON de PubTator."""
        return self.adapter.generate_kb(document)
