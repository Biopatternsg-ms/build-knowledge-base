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
import logging
from minio import Minio

logger = logging.getLogger("build-knowledge-base.minio_client")

_minio_instance: Minio | None = None


def get_minio_client() -> Minio:
    """
    Retorna el cliente MinIO como singleton.
    Lee la configuración desde variables de entorno inyectadas por Jenkins.
    """
    global _minio_instance
    if _minio_instance is None:
        endpoint   = os.environ.get("MINIO_ENDPOINT", "localhost:10000")
        access_key = os.environ.get("MINIO_ACCESS_KEY")
        secret_key = os.environ.get("MINIO_SECRET_KEY")

        if not access_key or not secret_key:
            logger.warning(
                "MINIO_ACCESS_KEY o MINIO_SECRET_KEY no están configuradas. "
                "Usando credenciales de desarrollo por defecto (minioadmin)."
            )
            access_key = access_key or "minio-user"
            secret_key = secret_key or "+h361R&_85Ac"

        _minio_instance = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False   # TLS se gestiona a nivel de red/proxy en producción
        )
        logger.info(f"Cliente MinIO inicializado — endpoint: {endpoint}")

    return _minio_instance


def get_bucket_name() -> str:
    """Retorna el nombre del bucket configurado."""
    return os.environ.get("MINIO_BUCKET", "biopatternsg-kb")
