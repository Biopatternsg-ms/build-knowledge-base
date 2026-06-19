# Guía de Ejecución Local y Pruebas del Microservicio `build-knowledge-base`

Esta guía detalla los pasos para levantar y probar el microservicio localmente en el entorno WSL (Debian) sin necesidad de Docker, permitiendo realizar consultas directamente desde Postman u otras herramientas de desarrollo en tu máquina Windows.

---

## Requisitos Previos

Asegúrate de estar en el directorio raíz del microservicio dentro de tu terminal de WSL:
```bash
cd /home/debian/nuevos-ms/build-knowledge-base
```

---

## Paso 1: Configurar el Entorno Virtual Python

Es recomendable crear un entorno virtual para aislar las dependencias del proyecto de tu instalación global de Python:

1. **Crear el entorno virtual:**
   ```bash
   python3 -m venv .venv
   ```

2. **Activar el entorno virtual:**
   ```bash
   source .venv/bin/activate
   ```
   *Nota: Tras la activación, verás el prefijo `(.venv)` al inicio de tu prompt en la terminal.*

---

## Paso 2: Instalar Dependencias

Instala los módulos de Python requeridos (FastAPI, Uvicorn, NLTK, regex) usando `pip`:

```bash
pip install -r requirements.txt
```

---

## Paso 3: Levantar el Servidor de Desarrollo

Inicia el servidor local con `uvicorn`. Se configura para escuchar en la interfaz local global (`0.0.0.0`) de modo que sea accesible desde Windows, usando el puerto `8007` y activando la recarga automática en caliente (`--reload`):

```bash
uvicorn main:app --host 0.0.0.0 --port 8007 --reload
```

---

## Paso 4: Pruebas con Postman (desde Windows)

Dado que WSL comparte el direccionamiento de red local (`localhost`) con el host de Windows, puedes abrir Postman en tu PC y consumir los endpoints utilizando las siguientes configuraciones:

### 1. Endpoint: `/hello` (GET)
* **Método:** `GET`
* **URL:** `http://localhost:8007/hello`
* **Respuesta Esperada (JSON):**
  ```json
  {
    "message": "hello"
  }
  ```

### 2. Endpoint: `/generate-pathways` (POST - Modo Directo)
* **Método:** `POST`
* **URL:** `http://localhost:8007/generate-pathways`
* **Headers:** `Content-Type: application/json`
* **Cuerpo (Body -> raw -> JSON):**
  ```json
  {
    "pathways": [
      "'A', 'activates', 'B'",
      "'B', 'inhibits', 'C'"
    ]
  }
  ```
* **Respuesta Esperada (JSON):**
  ```json
  {
    "status": "success",
    "processed_events_count": 2,
    "prolog_kb": "base([\nevent('A', 'activates', 'B'),\nevent('B', 'inhibits', 'C')\n])."
  }
  ```

### 3. Endpoint: `/generate-pathways` (POST - Modo Local en Servidor)
Este modo asume la existencia de un archivo `pathways.txt` en una carpeta local de la máquina virtual/servidor.
* **Método:** `POST`
* **URL:** `http://localhost:8007/generate-pathways`
* **Headers:** `Content-Type: application/json`
* **Cuerpo (Body -> raw -> JSON):**
  ```json
  {
    "root_path": "/ruta/de/la/carpeta/donde/esta/el/pathways.txt"
  }
  ```
* **Respuesta Esperada (JSON):**
  Generará el archivo `kb_pathways.pl` en esa misma ruta y responderá con:
  ```json
  {
    "status": "success",
    "processed_events_count": N,
    "prolog_kb": "base([ ... ])."
  }
  ```

---

## Desactivar el Entorno Virtual

Cuando termines tu sesión de desarrollo, puedes salir del entorno virtual simplemente ejecutando:
```bash
deactivate
```
