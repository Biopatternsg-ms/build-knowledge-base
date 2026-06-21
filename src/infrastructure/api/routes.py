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

logger = logging.getLogger("build-knowledge-base.routes")
router = APIRouter()

class HelloResponse(BaseModel):
    message: str
    version: str
    status: str

def get_hello_use_case() -> GetHelloMessageUseCase:
    repository = MockHelloRepository()
    return GetHelloMessageUseCase(repository)

@router.get("/hello", response_model=HelloResponse)
def read_hello(use_case: GetHelloMessageUseCase = Depends(get_hello_use_case)):
    logger.info("Endpoint /hello fue consultado exitosamente a través de la arquitectura limpia")
    hello_msg = use_case.execute()
    return HelloResponse(
        message=hello_msg.message,
        version=hello_msg.version,
        status=hello_msg.status
    )
