import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Build Knowledge Base Service",
    description="Servicio para construir bases de conocimiento y procesar pathways",
    version="1.0.0"
)

class PathwaysRequest(BaseModel):
    root_path: Optional[str] = None
    pathways: Optional[List[str]] = None

@app.get("/hello")
def read_hello():
    return {"message": "hello"}

    # Validar que al menos una entrada esté provista
    if not request.root_path and not request.pathways:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar 'root_path' para modo local o una lista de 'pathways' para procesamiento directo."
        )

    pathways_events = []

    # 1. Modo Local (lee de archivo local en el servidor si se indica root_path)
    if request.root_path:
        pathways_path = os.path.join(request.root_path, 'pathways.txt')
        kb_events_path = os.path.join(request.root_path, 'kb_pathways.pl')

        if not os.path.exists(pathways_path):
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontró el archivo 'pathways.txt' en la ruta especificada: {request.root_path}"
            )

        try:
            with open(pathways_path, 'r', encoding="utf8") as pp:
                lines = [line.strip() for line in pp.readlines()]
            
            for line in lines:
                if line.startswith("'"):
                    events = line.split(";")
                    for event in events:
                        if event not in pathways_events:
                            pathways_events.append(event)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al leer pathways.txt: {str(e)}")

    # 2. Modo Directo / Adicional (procesa la lista enviada en el JSON)
    if request.pathways:
        for line in request.pathways:
            line_clean = line.strip()
            # Mismo parsing que el script original
            if line_clean.startswith("'"):
                events = line_clean.split(";")
                for event in events:
                    if event not in pathways_events:
                        pathways_events.append(event)

    if not pathways_events:
        return {"status": "success", "message": "No se encontraron eventos para procesar.", "prolog_kb": "base([])."}

    # Generar contenido de Prolog
    prolog_lines = ["base(["]
    for event in pathways_events[:-1]:
        new_event = f"event({event})"
        prolog_lines.append(f"{new_event},")
    else:
        new_event = f"event({pathways_events[-1]})"
        prolog_lines.append(new_event)
    prolog_lines.append("]).")

    prolog_content = "\n".join(prolog_lines)

    # Si estamos en Modo Local, escribir el archivo kb_pathways.pl
    if request.root_path:
        try:
            kb_events_path = os.path.join(request.root_path, 'kb_pathways.pl')
            with open(kb_events_path, 'w', encoding="utf8") as kb_p:
                kb_p.write(prolog_content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al escribir kb_pathways.pl: {str(e)}")

    return {
        "status": "success",
        "processed_events_count": len(pathways_events),
        "prolog_kb": prolog_content
    }
