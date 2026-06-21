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
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_generate_kb_from_json():
    # Limpiar el directorio de salida si ya existe
    output_dir = "resources/output"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    payload = {
        "pmid": "9724159",
        "title": "Tolerance and antiviral effects of high-dose interferon-alpha B/D in patients with chronic hepatitis B.",
        "text": "A novel recombinant interferon-alpha B/D hybrid was applied to assess tolerability, antiviral effect, and biological activity in chronic hepatitis B. The study was designed as an open nonrandomized trial. Treatment comprised a two-week run-in phase with 16 MU three times a week followed by 14 weeks with 64 MU three times a week (or 48 MU if toxicity occurred with 64 MU). Total follow-up was 36 weeks. Nineteen patients were included; three discontinued treatment during the run-in with 16 MU. Fourteen of 16 patients had 14 weeks of treatment with > or = 32 MU three times a week. Fourteen dose reductions were necessary in nine patients. The adverse experience profile was similar to other interferon-alphas. HBV-DNA decreased using all doses studied. HBV-DNA became undetectable in five patients, two of whom had HBeAg seroconversion. No HBsAg seroconversion was observed. It is concluded that interferon-alpha B/D is well tolerated in high doses. The anti-viral effect starts at at least 16 MU three times a week.",
        "objects": [
            {
                "accession": "@GENE_IFNA8",
                "biotype": "gene",
                "identifier": "3445;3439",
                "locations": [
                    {
                        "length": 20,
                        "offset": 45
                    },
                    {
                        "length": 20,
                        "offset": 124
                    },
                    {
                        "length": 20,
                        "offset": 1003
                    }
                ],
                "name": "IFNA8",
                "normalizedId": "3445",
                "text": "interferon-alpha B/D",
                "type": "Gene"
            },
            {
                "accession": "@DISEASE_Hepatitis_B_Chronic",
                "biotype": "disease",
                "identifier": "MESH:D019694",
                "locations": [
                    {
                        "length": 20,
                        "offset": 83
                    },
                    {
                        "length": 20,
                        "offset": 233
                    }
                ],
                "name": "Hepatitis B Chronic",
                "normalizedId": "D019694",
                "text": "chronic hepatitis B.",
                "type": "Disease"
            },
            {
                "accession": "@DISEASE_Drug_Related_Side_Effects_and_Adverse_Reactions",
                "biotype": "disease",
                "identifier": "MESH:D064420",
                "locations": [
                    {
                        "length": 8,
                        "offset": 447
                    }
                ],
                "name": "Drug-Related Side Effects and Adverse Reactions",
                "normalizedId": "D064420",
                "text": "toxicity",
                "type": "Disease"
            }
        ],
        "events": [
            {
                "relationType": "Negative_Correlation",
                "role1": "@DISEASE_Hepatitis_B_Chronic",
                "role2": "@GENE_IFNA8"
            }
        ]
    }

    response = client.post("/generate-kb", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert data["output_directory"] == output_dir

    # Verificar que los archivos de salida se hayan creado
    assert os.path.exists(os.path.join(output_dir, "kBase.pl"))
    assert os.path.exists(os.path.join(output_dir, "kBaseDoc.txt"))
    assert os.path.exists(os.path.join(output_dir, "synonyms.pl"))
    assert os.path.exists(os.path.join(output_dir, "aligned.pl"))
    assert os.path.exists(os.path.join(output_dir, "biotypes-kbs", "biotypes.pl"))

    # Validar el contenido de kBase.pl
    with open(os.path.join(output_dir, "kBase.pl"), 'r', encoding="utf8") as f:
        kb_content = f.read()
        # Debe contener el evento procesado en formato Prolog
        assert "event('HEPATITIS B CHRONIC',negative_correlation,'IFNA8')" in kb_content
        # Y también el opuesto por ser tipo Negative_Correlation
        assert "event('IFNA8',negative_correlation,'HEPATITIS B CHRONIC')" in kb_content

    # Validar el contenido de biotypes.pl
    with open(os.path.join(output_dir, "biotypes-kbs", "biotypes.pl"), 'r', encoding="utf8") as f:
        biotypes_content = f.read()
        assert "protein('IFNA8')." in biotypes_content
        assert "disease('HEPATITIS B CHRONIC')." in biotypes_content
