# Arquitectura del Sistema KB — Build Knowledge Base

## Visión General

El sistema construye bases de conocimiento en formato Prolog a partir de resultados de PubTator (anotaciones biomédicas de artículos PubMed). Los archivos generados se almacenan de forma persistente en **MinIO** (object storage S3-compatible), organizados por `pipelineId`. El usuario puede descargarlos, editarlos y re-cargarlos desde la UI.

---

## Diagrama de Arquitectura

```mermaid
graph TB
    subgraph UI["🖥️ UI (biopatternsg-ui)"]
        USER["Usuario"]
    end

    subgraph PI["pubmed-integration (Java / Quarkus)"]
        UC["GenerateKbForPipeline\nUseCase"]
        MONGO_CLIENT["MongoDB Client"]
    end

    subgraph BKB["build-knowledge-base (Python / FastAPI)"]
        direction TB
        subgraph API_LAYER["Infrastructure — API"]
            ROUTES["routes.py\n/generate-kb\n/pipeline/{id}/kb/{file}"]
        end
        subgraph APP_LAYER["Application — Use Cases"]
            GEN_UC["GenerateKbUseCase"]
            DL_UC["DownloadKbUseCase"]
            UL_UC["UploadKbUseCase"]
        end
        subgraph INFRA_LAYER["Infrastructure — Adapters"]
            KB_GEN["PubTatorKbAdapter\n(generator)"]
            STORAGE["KbStorageAdapter\n(MinIO)"]
            MINIO_CLI["MinioClient\n(singleton)"]
        end
        subgraph MODEL_LAYER["Model — Domain"]
            PT_DOC["PubTatorDocument\n+ pipelineId"]
            PT_OBJ["PubTatorObject"]
            PT_EVT["PubTatorEvent"]
        end
    end

    subgraph STORAGE_LAYER["Infraestructura de Almacenamiento"]
        MONGODB[("MongoDB\npubmed_results\npubtator_results")]
        MINIO[("MinIO\nbucket: biopatternsg-kb\npipelines/{pipelineId}/\n  kbase.pl\n  synonyms.pl\n  aligned.pl\n  biotypes/biotypes.pl")]
    end

    USER -->|"Descarga kbase.pl"| UI
    USER -->|"Re-carga kbase.pl editado"| UI
    UI -->|"GET /pipeline/{id}/kb/kbase.pl"| ROUTES
    UI -->|"PUT /pipeline/{id}/kb/kbase.pl"| ROUTES

    UC -->|"POST /generate-kb\n{pipelineId, pmid, ...}"| ROUTES
    MONGO_CLIENT -->|"Lee pubmed_results\npubtator_results"| MONGODB

    ROUTES --> GEN_UC
    ROUTES --> DL_UC
    ROUTES --> UL_UC

    GEN_UC --> KB_GEN
    GEN_UC --> STORAGE
    DL_UC --> STORAGE
    UL_UC --> STORAGE

    STORAGE --> MINIO_CLI
    MINIO_CLI -->|"upload / download"| MINIO
```

---

## Capas de la Aplicación

### Model (Dominio)
Define las entidades y estructuras de datos sin dependencias externas.

| Archivo | Responsabilidad |
|---|---|
| `pubtator.py` | `PubTatorDocument`, `PubTatorObject`, `PubTatorEvent`, `Location` |
| `hello.py` | `HelloMessage` (entidad de demo) |
| `hello_repository.py` | Interfaz `HelloRepositoryInterface` |

### Application (Casos de Uso)
Orquesta la lógica de negocio. No conoce FastAPI ni MinIO directamente.

| Archivo | Responsabilidad |
|---|---|
| `generate_kb_use_case.py` | Genera KB para un documento, acumula en MinIO si hay `pipelineId` |
| `download_kb_use_case.py` | Descarga un archivo KB desde MinIO |
| `upload_kb_use_case.py` | Re-carga un archivo KB editado al MinIO |
| `get_hello_message.py` | Demo: retorna mensaje de saludo |

### Infrastructure (Adaptadores)
Implementaciones concretas de tecnologías externas.

| Archivo | Responsabilidad |
|---|---|
| `api/routes.py` | Endpoints FastAPI |
| `generator/pubtator_kb_adapter.py` | Genera archivos `.pl` a partir de documentos PubTator |
| `storage/minio_client.py` | Cliente MinIO singleton (configurado por env vars) |
| `storage/kb_storage_adapter.py` | Abstracción sobre MinIO: upload, download, exists |
| `repositories/mock_hello_repository.py` | Repositorio mock de demo |

---

## Estructura de Archivos en MinIO

```
bucket: biopatternsg-kb
└── pipelines/
    └── {pipelineId}/
        ├── kbase.pl              ← Base de conocimiento en Prolog
        ├── synonyms.pl           ← Sinónimos de entidades
        ├── aligned.pl            ← Objetos alineados con IDs PubTator
        └── biotypes/
            └── biotypes.pl       ← Identidades biológicas (protein, gene, etc.)
```

---

## Variables de Entorno

Todas las configuraciones sensibles se inyectan como variables de entorno desde Jenkins. No hay credenciales hardcodeadas en el repositorio.

| Variable | Descripción | Ejemplo |
|---|---|---|
| `MINIO_ENDPOINT` | Host y puerto del servidor MinIO | `minio:9000` |
| `MINIO_ACCESS_KEY` | Usuario / Access Key de MinIO | `(desde Jenkins)` |
| `MINIO_SECRET_KEY` | Contraseña / Secret Key de MinIO | `(desde Jenkins)` |
| `MINIO_BUCKET` | Nombre del bucket | `biopatternsg-kb` |

---

## Tecnologías

| Componente | Tecnología |
|---|---|
| API | FastAPI (Python 3.11) |
| Server | Uvicorn |
| Object Storage | MinIO (S3-compatible) |
| SDK MinIO | `minio>=7.2.0` (Python) |
| NLP | NLTK (tokenización de oraciones) |
| CI/CD | Jenkins |
| Containerización | Docker |
