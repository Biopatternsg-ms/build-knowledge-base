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
import io
import logging
from minio.error import S3Error
from src.infrastructure.storage.minio_client import get_minio_client, get_bucket_name

logger = logging.getLogger("build-knowledge-base.kb_storage_adapter")

# Prefijo base para todos los archivos KB en el bucket
_PIPELINE_PREFIX = "pipelines"


class KbStorageAdapter:
    """
    Adaptador de almacenamiento que gestiona los archivos KB en MinIO.
    Los archivos se organizan bajo: pipelines/{pipeline_id}/{filename}
    """

    def __init__(self):
        self.client = get_minio_client()
        self.bucket = get_bucket_name()
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Crea el bucket si no existe. Se ejecuta al inicializar el adaptador."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                logger.info(f"Bucket '{self.bucket}' creado exitosamente")
            else:
                logger.debug(f"Bucket '{self.bucket}' ya existe")
        except S3Error as e:
            logger.error(f"Error verificando/creando bucket '{self.bucket}': {e}")
            raise

    def _object_key(self, pipeline_id: str, filename: str) -> str:
        """Construye la clave del objeto en MinIO."""
        return f"{_PIPELINE_PREFIX}/{pipeline_id}/{filename}"

    def upload(self, pipeline_id: str, filename: str, data: bytes) -> None:
        """
        Sube o reemplaza un archivo KB para el pipeline dado.

        Args:
            pipeline_id: Identificador del pipeline.
            filename: Nombre del archivo (ej: 'kbase.pl', 'biotypes/biotypes.pl').
            data: Contenido del archivo en bytes.
        """
        key = self._object_key(pipeline_id, filename)
        try:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=key,
                data=io.BytesIO(data),
                length=len(data),
                content_type="text/plain"
            )
            logger.info(f"Archivo subido a MinIO: {key} ({len(data)} bytes)")
        except S3Error as e:
            logger.error(f"Error subiendo archivo a MinIO [{key}]: {e}")
            raise

    def download(self, pipeline_id: str, filename: str) -> bytes | None:
        """
        Descarga un archivo KB desde MinIO.

        Args:
            pipeline_id: Identificador del pipeline.
            filename: Nombre del archivo a descargar.

        Returns:
            Contenido del archivo como bytes, o None si no existe.
        """
        key = self._object_key(pipeline_id, filename)
        try:
            response = self.client.get_object(self.bucket, key)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"Archivo descargado de MinIO: {key} ({len(data)} bytes)")
            return data
        except S3Error as e:
            if e.code == "NoSuchKey":
                logger.debug(f"Archivo no encontrado en MinIO: {key}")
                return None
            logger.error(f"Error descargando archivo de MinIO [{key}]: {e}")
            raise

    def exists(self, pipeline_id: str, filename: str) -> bool:
        """
        Verifica si un archivo existe en MinIO para el pipeline dado.

        Args:
            pipeline_id: Identificador del pipeline.
            filename: Nombre del archivo.

        Returns:
            True si el archivo existe, False en caso contrario.
        """
        key = self._object_key(pipeline_id, filename)
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except S3Error as e:
            if e.code == "NoSuchKey":
                return False
            logger.error(f"Error verificando existencia de archivo [{key}]: {e}")
            raise
