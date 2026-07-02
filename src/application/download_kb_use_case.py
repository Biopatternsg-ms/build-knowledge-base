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

logger = logging.getLogger("build-knowledge-base.download_kb_use_case")


class DownloadKbUseCase:
    def __init__(self, storage: KbStorageAdapter):
        self.storage = storage

    def execute(self, pipeline_id: str, filename: str) -> bytes | None:
        logger.info(f"Descargando archivo '{filename}' para pipeline={pipeline_id}")
        return self.storage.download(pipeline_id, filename)
