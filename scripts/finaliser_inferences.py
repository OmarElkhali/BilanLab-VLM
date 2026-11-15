"""Exécute le schéma minimal et la relecture séparée, sans changer le benchmark."""
from datetime import datetime, timezone
import getpass
import json
import os
import sys
import time
from pathlib import Path
import nbformat

sys.stdout.reconfigure(encoding='utf-8')

root=Path(__file__).resolve().parent.parent
os.chdir(root)
secret=os.getenv('GEMINI_API_KEY') or getpass.getpass('Cle Gemini (saisie masquee) : ')
os.environ['GEMINI_API_KEY']=secret.strip()
nb=nbformat.read(root/'TP_Extraction_Bilans_VLM_Groupe9.ipynb',as_version=4)
ns={'__name__':'__main__'}
prefixes=['# Copie du PDF fourni','from pathlib import Path\nfrom decimal import Decimal, InvalidOperation',
    'def sha256_file','# Rectangles normalisés','def improve_contrast','COLUMNS =','REFERENCE_TABLE =','records =',
    'SYSTEM_ROLE =','def validate_page','GEMINI_API_KEY =','def check_local_url','def local_map_schema',
    'RUN_LOGS =','def calculation_amount','TP_MINIMAL_LINE_SCHEMA =','def review_flagged']
for prefix in prefixes:
    cells=[c for c in nb.cells if c.cell_type=='code' and c.source.startswith(prefix)]
    if len(cells)!=1:raise ValueError('Cellule absente ou ambiguë : '+prefix)
    exec(compile(cells[0].source,'<notebook:'+prefix.splitlines()[0]+'>','exec'),ns)
ns.update(RUN_API=True,API_IMAGES_REVIEWED=True)
minimal=ns['extract_tp_minimal']()
print('Schéma minimal réellement exécuté :',[len(p['lignes']) for p in minimal['pages']],flush=True)
campaign_path=root/'outputs_vlm/campagne_courante.json'
campaign=json.loads(campaign_path.read_text(encoding='utf-8'))
principal=next(r for r in ns['CURRENT_RESULTS'] if r['label']=='principal_valide')
if not principal['document_complet'] or any(c['statut'] in ['ecart','indetermine'] for c in ns['arithmetic_checks'](principal)):
    proposals=ns['review_flagged'](principal,ns['IMAGES'])
    print('Relecture séparée :',len(proposals or []),'propositions ; résultat initial inchangé.',flush=True)
# Exécution de livraison après l'incident de connexion : explicitement hors benchmark.
result=ns['run_document'](ns['PDF_PATH'],ns['IMAGES'],'api','schema',validation_retries=1,label='principal_relecture')
result['campaign_id']=campaign['id']
result['hors_benchmark']=True
result['justification']='Nouvelle extraction de livraison après le premier incident de connexion ; échec initial et benchmark conservés.'
ns['dump_json'](Path(result['run_dir'])/'bilan.json',result)
# Le moteur local peut encore écrire son manifeste : attendre sa fin avant la mise à jour.
while True:
    current=json.loads(campaign_path.read_text(encoding='utf-8'))
    if current['id']!=campaign['id']:raise RuntimeError('La campagne a changé pendant la finalisation.')
    if current['statut']!='en_cours':campaign=current;break
    time.sleep(5)
campaign['experiences'].append({'backend':'api','variante':'schema','label':result['label'],
    'run_dir':str(Path(result['run_dir']).relative_to(root)),'complet':result['document_complet']})
campaign['finalisation_utc']=datetime.now(timezone.utc).isoformat()
campaign['schema_minimal']=True
campaign_path.write_text(json.dumps(campaign,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
os.environ.pop('GEMINI_API_KEY',None)
print('Finalisation réellement exécutée, complète :',result['document_complet'],flush=True)
