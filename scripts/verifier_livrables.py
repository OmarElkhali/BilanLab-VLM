"""Verification hors inference des livrables, puis archive ZIP de remise."""
import ast
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import zipfile

import nbformat
import jsonschema

root = Path(__file__).resolve().parent.parent
path = root / 'TP_Extraction_Bilans_VLM_Groupe9.ipynb'
notebook = nbformat.read(path, as_version=4)
nbformat.validate(notebook)
code_cells = [cell for cell in notebook.cells if cell.cell_type == 'code']
assert all(cell.execution_count is not None for cell in code_cells), 'Cellules non executees.'
assert not any(output.output_type == 'error' for cell in code_cells for output in cell.outputs), 'Erreur dans une sortie.'
for cell in code_cells:
    ast.parse(cell.source)

out = root / 'outputs_vlm'
read = lambda name: json.loads((out / name).read_text(encoding='utf-8-sig'))
schema = read('schema_metier_page.json')
reference = read('reference_annotee.json')
gold = {row['id']: row for row in reference['lignes']}
main = read('bilan_group_9_extrait.json')
assert main['document_complet'] is True
assert main['source_sha256'] == hashlib.sha256((root/'bilan_group_9.pdf').read_bytes()).hexdigest()
actual = {}
for page in main['pages']:
    jsonschema.validate({k:v for k,v in page.items() if k != 'page'}, schema)
    assert page['exercice_N'] == 2024
    for row in page['lignes']:
        assert row['id'] not in actual
        actual[row['id']] = row
assert set(actual) == set(gold) and len(actual) == 88
numeric = 0
for identifier, expected in gold.items():
    row = actual[identifier]
    for column in ['montant_brut_N','montant_amort_N','montant_net_N','montant_net_N1']:
        assert row['etats'][column] == expected['etats'][column]
        if expected[column] is None:
            assert row[column] is None
        else:
            assert Decimal(row[column]) == Decimal(expected[column])
            numeric += 1
assert numeric == 107
folder = PureWindowsPath(main['run_dir']).name if '\\' in main['run_dir'] else Path(main['run_dir']).name
checks = json.loads((out/'runs'/folder/'controles_comptables.json').read_text(encoding='utf-8'))
assert sum(c['statut']=='ok' for c in checks) == 66
assert not any(c['statut'] in ['ecart','indetermine'] for c in checks)
batch = read('batch_manifest.json')
assert len(batch) == 2 and all(row['complet'] for row in batch)
summary = read('resultats_finaux.json')
assert len([r for r in summary if r['experience']=='ablation_validee_1']) == 6
assert any(r['backend']=='local' for r in summary)
assert any(r['experience']=='scan_degrade_valide' for r in summary)
campaign = read('campagne_courante.json')
assert campaign['statut'] == 'terminee'
benchmark = [r for r in summary if r['experience'].startswith('ablation_validee_')]
assert len(benchmark) == 18, 'Il faut six strategies et trois repetitions.'
assert len({(r['variante'],r['experience']) for r in benchmark}) == 18
minimal = read('bilan_group_9_TP_minimal.json')
assert len(minimal['pages']) == 2
assert all(set(row) == {'poste','rubrique','montant_net_N','montant_net_N1'} for page in minimal['pages'] for row in page['lignes'])
figures = list((out/'figures').glob('*.png'))
assert len(figures) >= 10
html_path = root/'TP_Extraction_Bilans_VLM_Groupe9.html'
assert html_path.is_file()

files = [root/'TP_Extraction_Bilans_VLM_Groupe9.ipynb', root/'bilan_group_9.pdf',
         root/'TP5_Extraction_Bilans_VLM.docx', root/'README.md', root/'requirements.txt',
         root/'requirements-lock.txt',root/'requirements-local.txt',root/'.gitignore',html_path,root/'demarrer_application.cmd',
         root/'webapp/outputs/resultats-live.png']
files += sorted(p for p in (root/'scripts').rglob('*.py') if p.is_file())
files += sorted(p for p in out.rglob('*') if p.is_file())
deck = root/'BilanLab_Presentation_21'
files += sorted(p for p in deck.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.lock'))
local_summary = read('optimisation_locale/synthese.json')
assert len(local_summary['trials']) == 3
assert all(r['numeric_correct'] == 107 and r['erreurs_cellules'] == 0 and r['controles_ok'] == 66 for r in local_summary['trials'])
# L'application fait partie du projet ; aucun environnement, cache ou secret n'est archivé.
excluded = {'node_modules','.git','.wrangler','.vinext','.sites-runtime','dist','outputs','work','.agents','.codex','__pycache__'}
files += sorted(p for p in (root/'webapp').rglob('*') if p.is_file()
                and not excluded.intersection(p.relative_to(root/'webapp').parts)
                and not p.name.startswith(('.env','.dev.vars'))
                and not p.name.endswith(('.tsbuildinfo','.pem','.log')))
secret = os.getenv('GEMINI_API_KEY','').encode()
if secret:
    assert not any(secret in p.read_bytes() for p in files), 'Secret detecte dans un livrable.'
verification = {'statut':'OK','cellules_code_executees':len(code_cells),'erreurs_notebook':0,
                'lignes_reference':88,'montants_strictement_exacts':107,'controles_comptables_ok':66,
                'entrees_lot_reussies':2,'bilans_reels_distincts':1,
                'experiences_archivees':len(list((out/'runs').glob('*/bilan.json'))),
                'essais_benchmark_courants':len(benchmark),'figures_supplementaires':len(figures),
                'schema_minimal_tp':True,'export_html_autonome':True,
                'cle_api_incluse':False,'local_hybride_median_s':local_summary['median_seconds'],
                'local_hybride_montants_exacts':107,'local_hybride_essais':3,
                'limite_locale':'Qwen seul negatif conserve ; hybride OCR + Qwen exact sur un seul bilan, Qwen deja charge'}
(out/'verification_livrables.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files.append(out/'verification_livrables.json')
files = sorted(set(files))
manifest = {str(p.relative_to(root)).replace('\\','/'):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'octets':p.stat().st_size} for p in files}
manifest_path = root/'manifest_projet.json'
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
archive = root/'Projet_VLM_Groupe9_Complet.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,strict_timestamps=False) as output:
    for file in files + [manifest_path]:
        output.write(file,arcname=file.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as saved:
    assert saved.testzip() is None
print(json.dumps({**verification,'archive':archive.name,'taille_zip_octets':archive.stat().st_size},ensure_ascii=False))
