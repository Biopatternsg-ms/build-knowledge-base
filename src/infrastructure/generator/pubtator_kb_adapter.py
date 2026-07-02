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
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import nltk
from src.model.pubtator import PubTatorDocument

logger = logging.getLogger("build-knowledge-base.pubtator_kb_adapter")

# Relaciones simétricas especiales que generan eventos inversos
SPECIAL_RELATIONS = ['positive_correlation', 'negative_correlation']

def get_event_sents(sentences: List[str], event: Dict[str, Any], entities: Dict[str, List[Dict[str, Any]]], pubmed_id: str, abstract: str) -> List[Tuple[str, str]]:
    subject = event['subject']
    object = event['object']

    subject_entities = entities.get(subject, [])
    object_entities = entities.get(object, [])

    subject_names = []
    object_names = []
    relation_sents = []

    for sub_ent in subject_entities:
        sub_name = sub_ent['text']
        if sub_name not in subject_names:
            subject_names.append(sub_name)

    for obj_ent in object_entities:
        obj_name = obj_ent['text']
        if obj_name not in object_names:
            object_names.append(obj_name)

    for sentence in sentences:
        for sub_name in subject_names:
            for obj_name in object_names:
                if sub_name in sentence and obj_name in sentence:
                    if (sentence, pubmed_id) not in relation_sents:
                        relation_sents.append((sentence, pubmed_id))

    if not relation_sents:
        relation_sents.append((abstract, pubmed_id))

    return relation_sents

def get_normalized_kb(events: Dict[str, Any], entities: Dict[str, List[Dict[str, Any]]], objects_identities: List[Tuple[str, str]], output_dir: str) -> Tuple[Dict[str, Any], Dict[str, List[str]]]:
    knowledge_base = {}
    object_synonyms = {}
    
    biotypes_dir = os.path.join(output_dir, "biotypes-kbs")
    os.makedirs(biotypes_dir, exist_ok=True)
    biotypes_path = os.path.join(biotypes_dir, "biotypes.pl")

    with open(biotypes_path, 'w', encoding="utf8") as biotypes_file:
        biotypes_file.write("% The identities for the objects present in the knowledge base, as pubtator predicts them.\n\n")
        for _, identity in objects_identities:
            biotypes_file.write(identity + "\n")

    for key, values in events.items():
        subject = values['subject']
        object = values['object']
        relation = values['relation']
        
        subject_entities = entities.get(subject, [])
        object_entities = entities.get(object, [])
        
        subject_names = [subject]
        object_names = [object]

        for sub_ent in subject_entities:
            sub_name = sub_ent['name']
            if sub_name not in subject_names:
                subject_names.append(sub_name)
            if sub_ent['ID'] not in subject_names:
                subject_names.append(sub_ent['ID'])
            if sub_ent['text'] not in subject_names:
                subject_names.append(sub_ent['text'])

        if subject not in object_synonyms:
            object_synonyms[subject] = subject_names

        for obj_ent in object_entities:
            obj_name = obj_ent['name']
            if obj_name not in object_names:
                object_names.append(obj_name)
            if obj_ent['ID'] not in object_names:
                object_names.append(obj_ent['ID'])
            if obj_ent['text'] not in object_names:
                object_names.append(obj_ent['text'])

        if object not in object_synonyms:
            object_synonyms[object] = object_names

        new_event = f"event('{subject}',{relation},'{object}')"
        knowledge_base[new_event] = values
        knowledge_base[new_event]['names'] = (subject_names, object_names)

    return knowledge_base, object_synonyms

def print_kb(knowledge_base: Dict[str, Any], output_dir: str) -> None:
    kb_path = os.path.join(output_dir, "kBase.pl")
    doc_kb_path = os.path.join(output_dir, "kBaseDoc.txt")

    events_count = 0
    with open(kb_path, 'w', encoding="utf8") as kb:
        kb.write("base([\n")
        for event, values in knowledge_base.items():
            events_count += 1
            if values['opposite']:
                kb.write(values['opposite'] + ",\n")
            if events_count != len(knowledge_base):
                kb.write(event + ",\n")
            else:
                kb.write(event + "\n")
                kb.write("]).")

    with open(doc_kb_path, 'w', encoding="utf8") as kb_doc:
        for event, values in knowledge_base.items():
            subject_names, object_names = values['names']
            kb_doc.write("******************* Regulatory Event *******************\n\n")
            kb_doc.write(event + "\n\n")
            kb_doc.write(f"subject names: : {str(subject_names)}\n")
            kb_doc.write(f"object names: : {str(object_names)}\n\n")
            kb_doc.write("Sentences from abstracts:\n")
            kb_doc.write("------------------------\n\n")
            for sentence, pubmed_id in values['sentences']:
                kb_doc.write(sentence + " PUBMED_ID: " + pubmed_id + "\n\n")
            kb_doc.write("\n")

            if values['opposite']:
                kb_doc.write("******************* Regulatory Event *******************\n\n")
                kb_doc.write(values['opposite'] + "\n\n")
                kb_doc.write(f"subject names: : {str(object_names)}\n")
                kb_doc.write(f"object names: : {str(subject_names)}\n\n")
                kb_doc.write("Sentences from abstracts:\n")
                kb_doc.write("------------------------\n\n")
                for sentence, pubmed_id in values['sentences']:
                    kb_doc.write(sentence + " PUBMED_ID: " + pubmed_id + "\n\n")
                kb_doc.write("\n")

def print_synonyms(objects_synonyms: Dict[str, List[str]], output_dir: str) -> None:
    synonyms_path = os.path.join(output_dir, "synonyms.pl")
    with open(synonyms_path, 'w', encoding="utf8") as syms_fl:
        syms_fl.write("% Objects and their synonyms from Pubtator\n\n")
        for obj, synonyms in objects_synonyms.items():
            syms_fl.write(f"synonyms('{obj}', {synonyms}).\n")

def print_aligned_objs(output_dir: str, synonyms: Dict[str, List[str]], working_dir: str) -> None:
    aligned_objects_path = os.path.join(output_dir, "aligned.pl")
    with open(aligned_objects_path, 'w', encoding="utf8") as aligned_objs_fl:
        aligned_objs_fl.write("% The list of user's objects aligned and no aligned with the PubTator's IDs in the KB\n\n")
        aligned_objs_fl.write("% Aligned objects: \n\n")
        aligned_objs_fl.write("aligned(none).\n")
        aligned_objs_fl.write("\n% No aligned objects: \n\n")
        aligned_objs_fl.write("no_aligned(none).\n\n")
        aligned_objs_fl.write("\n% User's objects with alternative alignments: \n\n")
        aligned_objs_fl.write("aligned_as(none, none).\n")
        aligned_objs_fl.write("\n% General report of aligned and no aligned objects: \n\n")
        aligned_objs_fl.write("aligned_objs([], 0).\n\n")
        aligned_objs_fl.write("no_aligned_objs([], 0).\n\n")
        aligned_objs_fl.write("aligned_as([], 0).\n\n")
        aligned_objs_fl.write("aligned_and_alternatives([], 0).")

def print_species_pubmed_ids(output_dir: str, species_pubmed_ids: List[str]):
    species_pubmed_ids_path = os.path.join(output_dir, "species_pubmed_ids.txt")
    with open(species_pubmed_ids_path, 'w', encoding="utf8") as pubmed_ids_fl:
        for pubmed_id in species_pubmed_ids:
            pubmed_ids_fl.write(f"{pubmed_id}\n")

class PubTatorKbAdapter:
    def __init__(self, output_dir: str = "resources/output", working_dir: str = "."):
        self.output_dir = output_dir
        self.working_dir = working_dir

    def generate_kb(self, document: PubTatorDocument) -> str:
        # Asegurar existencia de directorio de salida
        os.makedirs(self.output_dir, exist_ok=True)
        
        logs_files_path = os.path.join(self.output_dir, "logs")
        if os.path.exists(logs_files_path):
            shutil.rmtree(logs_files_path)
        os.makedirs(logs_files_path, exist_ok=True)

        errors_file_path = os.path.join(logs_files_path, "errors.txt")
        errors = open(errors_file_path, 'w', encoding="utf8")

        try:
            # Combinar título y abstract
            abstract = document.title + "\n" + document.text
            sentences = nltk.sent_tokenize(abstract)
            pubmed_id = document.pmid

            entities = {}
            objects_identities = []
            species_pubmed_ids = []
            species_names = ["PSEUDOMONAS", "P. "]
            species_names_upper = [sp.upper() for sp in species_names]

            # Mapeo de accession a nombre estándar
            accession_to_name = {}

            for obj in document.objects:
                accession_id = obj.accession.replace("'", "\\'").upper()
                std_name = obj.name.replace("'", "\\'").upper()
                accession_to_name[obj.accession] = std_name
                accession_to_name[obj.accession.upper()] = std_name

                # Buscar especies de interés
                for spec_name in species_names_upper:
                    if spec_name in accession_id:
                        if pubmed_id not in species_pubmed_ids:
                            species_pubmed_ids.append(pubmed_id)

                for loc in obj.locations:
                    entity = {
                        'ID': std_name,
                        'start': loc.offset,
                        'end': loc.offset + loc.length,
                        'text': abstract[loc.offset:loc.offset + loc.length].replace("'", "\\'").upper(),
                        'name': std_name,
                        'type': obj.type,
                        'biotype': obj.biotype,
                        'pubmed_id': pubmed_id
                    }

                    if std_name not in entities:
                        entities[std_name] = [entity]
                        
                        biotype_lower = obj.biotype.lower()
                        if biotype_lower == 'gene':
                            objects_identities.append((std_name, f"protein('{std_name}')."))
                        elif biotype_lower == 'chemical':
                            objects_identities.append((std_name, f"ligand('{std_name}')."))
                        elif biotype_lower == 'disease':
                            objects_identities.append((std_name, f"disease('{std_name}')."))
                        elif biotype_lower == 'variant':
                            objects_identities.append((std_name, f"variant('{std_name}')."))
                        elif biotype_lower == 'species':
                            objects_identities.append((std_name, f"species('{std_name}')."))
                        elif biotype_lower == 'cellline':
                            objects_identities.append((std_name, f"cellline('{std_name}')."))
                    else:
                        entities[std_name].append(entity)

            # Procesar relaciones
            events = {}
            for ev in document.events:
                subj_accession = ev.role1
                obj_accession = ev.role2
                
                subj_name = accession_to_name.get(subj_accession, subj_accession.replace("'", "\\'").upper())
                obj_name = accession_to_name.get(obj_accession, obj_accession.replace("'", "\\'").upper())

                relation = ev.relationType.lower()
                event_data = {
                    'subject': subj_name,
                    'relation': relation,
                    'object': obj_name
                }
                
                event_tag = f"{subj_name},{relation},{obj_name}"
                event_sents = get_event_sents(sentences, event_data, entities, pubmed_id, abstract)

                if event_tag not in events:
                    opposite = None
                    event_data['pubmed_ids'] = [pubmed_id]
                    event_data['sentences'] = event_sents
                    if relation in SPECIAL_RELATIONS:
                        opposite = f"event('{obj_name}',{relation},'{subj_name}')"
                    event_data['opposite'] = opposite
                    events[event_tag] = event_data
                else:
                    prev_sents = [s for s, _ in events[event_tag]['sentences']]
                    for s, pm in event_sents:
                        if s not in prev_sents:
                            events[event_tag]['sentences'].append((s, pm))
                    events[event_tag]['pubmed_ids'].append(pubmed_id)

            # Normalizar base de conocimiento
            kb, synonyms = get_normalized_kb(events, entities, objects_identities, self.output_dir)

            # Escribir salidas
            print_kb(kb, self.output_dir)
            print_synonyms(synonyms, self.output_dir)
            print_aligned_objs(self.output_dir, synonyms, self.working_dir)
            
            if species_pubmed_ids:
                print_species_pubmed_ids(self.output_dir, species_pubmed_ids)

        except Exception as e:
            logger.error(f"Error generating KB from PubTator: {e}", exc_info=True)
            errors.write(f"Error processing document {document.pmid}: {str(e)}\n")
            raise e
        finally:
            errors.close()

        return self.output_dir

    def _process_document_to_structures(self, document: PubTatorDocument) -> tuple:
        """
        Procesa un documento PubTator y retorna las estructuras internas
        (entities, events, objects_identities) sin escribir nada al disco.
        Reutilizado por generate_kb_to_bytes y merge_kb_bytes.
        """
        abstract = document.title + "\n" + document.text
        sentences = nltk.sent_tokenize(abstract)
        pubmed_id = document.pmid

        entities: Dict[str, List[Dict[str, Any]]] = {}
        objects_identities: List[Tuple[str, str]] = []
        accession_to_name: Dict[str, str] = {}

        for obj in document.objects:
            std_name = obj.name.replace("'", "\\'").upper()
            accession_to_name[obj.accession] = std_name
            accession_to_name[obj.accession.upper()] = std_name

            for loc in obj.locations:
                entity = {
                    'ID': std_name,
                    'start': loc.offset,
                    'end': loc.offset + loc.length,
                    'text': abstract[loc.offset:loc.offset + loc.length].replace("'", "\\'").upper(),
                    'name': std_name,
                    'type': obj.type,
                    'biotype': obj.biotype,
                    'pubmed_id': pubmed_id
                }
                if std_name not in entities:
                    entities[std_name] = [entity]
                    biotype_lower = obj.biotype.lower()
                    type_map = {
                        'gene': f"protein('{std_name}').",
                        'chemical': f"ligand('{std_name}').",
                        'disease': f"disease('{std_name}').",
                        'variant': f"variant('{std_name}').",
                        'species': f"species('{std_name}').",
                        'cellline': f"cellline('{std_name}').",
                    }
                    if biotype_lower in type_map:
                        objects_identities.append((std_name, type_map[biotype_lower]))
                else:
                    entities[std_name].append(entity)

        events: Dict[str, Any] = {}
        for ev in document.events:
            subj_name = accession_to_name.get(ev.role1, ev.role1.replace("'", "\\'").upper())
            obj_name  = accession_to_name.get(ev.role2, ev.role2.replace("'", "\\'").upper())
            relation  = ev.relationType.lower()

            event_data = {'subject': subj_name, 'relation': relation, 'object': obj_name}
            event_tag  = f"{subj_name},{relation},{obj_name}"
            event_sents = get_event_sents(sentences, event_data, entities, pubmed_id, abstract)

            if event_tag not in events:
                opposite = f"event('{obj_name}',{relation},'{subj_name}')" if relation in SPECIAL_RELATIONS else None
                event_data['pubmed_ids'] = [pubmed_id]
                event_data['sentences']  = event_sents
                event_data['opposite']   = opposite
                events[event_tag] = event_data
            else:
                prev_sents = [s for s, _ in events[event_tag]['sentences']]
                for s, pm in event_sents:
                    if s not in prev_sents:
                        events[event_tag]['sentences'].append((s, pm))
                events[event_tag]['pubmed_ids'].append(pubmed_id)

        return entities, events, objects_identities

    def _structures_to_bytes(self, entities, events, objects_identities) -> Dict[str, bytes]:
        """
        Convierte las estructuras internas a un diccionario {filename: bytes}.
        No escribe nada al disco.
        """
        import tempfile, shutil as _shutil

        tmp_dir = tempfile.mkdtemp()
        try:
            kb, synonyms = get_normalized_kb(events, entities, objects_identities, tmp_dir)
            print_kb(kb, tmp_dir)
            print_synonyms(synonyms, tmp_dir)
            print_aligned_objs(tmp_dir, synonyms, self.working_dir)

            result: Dict[str, bytes] = {}
            for fname in ["kBase.pl", "kBaseDoc.txt", "synonyms.pl", "aligned.pl"]:
                fpath = os.path.join(tmp_dir, fname)
                if os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        result[fname] = f.read()

            biotypes_path = os.path.join(tmp_dir, "biotypes-kbs", "biotypes.pl")
            if os.path.exists(biotypes_path):
                with open(biotypes_path, 'rb') as f:
                    result["biotypes/biotypes.pl"] = f.read()

            return result
        finally:
            _shutil.rmtree(tmp_dir, ignore_errors=True)

    def generate_kb_as_json(self, document: PubTatorDocument) -> Dict[str, Any]:
        """
        Genera la base de conocimiento a partir de un documento PubTator y retorna
        toda la información como un diccionario Python estructurado (sin escribir
        al disco ni a MinIO).

        Returns:
            Diccionario con las claves:
              - events:   list[{event: str, pubmedIds: list[str]}]
              - synonyms: dict[str, list[str]]
              - aligned:  dict con la estructura de aligned.pl
              - biotypes: dict[str, str]  (nombre → tipo: protein, ligand, ...)
        """
        import re

        entities, events, objects_identities = self._process_document_to_structures(document)

        # ── Construir knowledge_base y synonyms en memoria ───────────────────
        knowledge_base: Dict[str, Any] = {}
        object_synonyms: Dict[str, List[str]] = {}

        for key, values in events.items():
            subject  = values['subject']
            object_  = values['object']
            relation = values['relation']

            subject_entities = entities.get(subject, [])
            object_entities  = entities.get(object_, [])

            subject_names = [subject]
            object_names  = [object_]

            for sub_ent in subject_entities:
                for field in ('name', 'ID', 'text'):
                    if sub_ent[field] not in subject_names:
                        subject_names.append(sub_ent[field])

            if subject not in object_synonyms:
                object_synonyms[subject] = subject_names

            for obj_ent in object_entities:
                for field in ('name', 'ID', 'text'):
                    if obj_ent[field] not in object_names:
                        object_names.append(obj_ent[field])

            if object_ not in object_synonyms:
                object_synonyms[object_] = object_names

            event_str = f"event('{subject}',{relation},'{object_}')"
            knowledge_base[event_str] = {**values, 'names': (subject_names, object_names)}

        # ── events: extraer first/relation/second y pubmedIds (lógica de kBaseDoc) ─
        events_json: List[Dict[str, Any]] = []
        for event_str, values in knowledge_base.items():
            subject  = values['subject']
            relation = values['relation']
            object_  = values['object']

            events_json.append({
                "event": {
                    "first":    subject,
                    "relation": relation,
                    "second":   object_,
                },
                "pubmedIds": values['pubmed_ids'],
            })
            if values.get('opposite'):
                # Relación simétrica: el evento inverso intercambia first y second
                events_json.append({
                    "event": {
                        "first":    object_,
                        "relation": relation,
                        "second":   subject,
                    },
                    "pubmedIds": values['pubmed_ids'],
                })

        # ── biotypes: extraer tipo desde la cadena "protein('NAME')." ──────────
        biotypes_json: Dict[str, str] = {}
        biotype_re = re.compile(r"^(\w+)\('")
        for name, identity_str in objects_identities:
            m = biotype_re.match(identity_str)
            if m:
                biotypes_json[name] = m.group(1)

        # ── aligned: estructura estática (equivale al contenido de aligned.pl) ─
        aligned_json: Dict[str, Any] = {
            "aligned":         ["none"],
            "no_aligned":      ["none"],
            "aligned_as":      [["none", "none"]],
            "aligned_objs":    {"items": [], "count": 0},
            "no_aligned_objs": {"items": [], "count": 0},
        }

        return {
            "events":   events_json,
            "synonyms": object_synonyms,
            "aligned":  aligned_json,
            "biotypes": biotypes_json,
        }

    def generate_kb_to_bytes(self, document: PubTatorDocument) -> Dict[str, bytes]:
        """
        Genera los archivos KB para un único documento y los retorna en memoria.
        No escribe al disco. Usado para la acumulación en MinIO.

        Returns:
            Diccionario {filename: bytes} con los archivos generados.
        """
        entities, events, objects_identities = self._process_document_to_structures(document)
        return self._structures_to_bytes(entities, events, objects_identities)

    def merge_kb_bytes(
        self,
        existing_bytes: Dict[str, bytes],
        document: PubTatorDocument
    ) -> Dict[str, bytes]:
        """
        Mergea el KB acumulado existente con un nuevo documento PubTator.
        Los eventos duplicados se deduplicam; las oraciones se acumulan.

        Args:
            existing_bytes: Archivos KB actuales en MinIO (pueden estar vacíos).
            document: Nuevo documento PubTator a agregar.

        Returns:
            Diccionario {filename: bytes} con el KB mergeado.
        """
        # Procesar el nuevo documento
        new_entities, new_events, new_objects_identities = self._process_document_to_structures(document)

        # Parsear el kBase.pl existente para recuperar los eventos acumulados
        # Estrategia: re-procesar a nivel de estructuras mergeando en memoria
        # Los eventos del nuevo documento se fusionan con los ya existentes

        # Recuperar entidades y eventos del acumulado parseando el kBase.pl existente
        existing_events: Dict[str, Any] = {}
        existing_entities: Dict[str, List[Dict[str, Any]]] = {}
        existing_identities: List[Tuple[str, str]] = []

        if "kBase.pl" in existing_bytes:
            # Parsear eventos del kBase.pl acumulado (formato: event('S',rel,'O'))
            import re
            kbase_text = existing_bytes["kBase.pl"].decode("utf-8", errors="replace")
            event_pattern = re.compile(r"event\('([^']+)',([^,]+),'([^']+)'\)")
            for match in event_pattern.finditer(kbase_text):
                subj, rel, obj = match.group(1), match.group(2), match.group(3)
                tag = f"{subj},{rel},{obj}"
                if tag not in existing_events:
                    opposite = f"event('{obj}',{rel},'{subj}')" if rel in SPECIAL_RELATIONS else None
                    existing_events[tag] = {
                        'subject': subj, 'relation': rel, 'object': obj,
                        'pubmed_ids': [], 'sentences': [], 'opposite': opposite,
                        'names': ([subj], [obj])
                    }

        if "biotypes/biotypes.pl" in existing_bytes:
            biotypes_text = existing_bytes["biotypes/biotypes.pl"].decode("utf-8", errors="replace")
            import re
            biotype_pattern = re.compile(r"(\w+)\('([^']+)'\)\.")
            for match in biotype_pattern.finditer(biotypes_text):
                btype, name = match.group(1), match.group(2)
                existing_identities.append((name, f"{btype}('{name}')."))

        # Mergear eventos nuevos sobre los existentes
        merged_events = {**existing_events}
        for tag, ev_data in new_events.items():
            if tag not in merged_events:
                merged_events[tag] = ev_data
            else:
                prev_sents = [s for s, _ in merged_events[tag]['sentences']]
                for s, pm in ev_data['sentences']:
                    if s not in prev_sents:
                        merged_events[tag]['sentences'].append((s, pm))
                merged_events[tag]['pubmed_ids'].extend(ev_data['pubmed_ids'])

        # Mergear entidades e identidades
        merged_entities = {**existing_entities, **new_entities}
        seen_names = {name for name, _ in existing_identities}
        merged_identities = list(existing_identities)
        for name, identity in new_objects_identities:
            if name not in seen_names:
                merged_identities.append((name, identity))
                seen_names.add(name)

        return self._structures_to_bytes(merged_entities, merged_events, merged_identities)
