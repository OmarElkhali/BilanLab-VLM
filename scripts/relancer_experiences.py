"""Nouvelle campagne réelle ; mêmes fonctions que le notebook, clé masquée en mémoire."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import getpass
import json
import os
from pathlib import Path
import random
import threading

import nbformat

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
secret = os.getenv('GEMINI_API_KEY') or getpass.getpass('Cle Gemini (saisie masquee) : ')
os.environ['GEMINI_API_KEY'] = secret.strip()
notebook = nbformat.read(ROOT/'TP_Extraction_Bilans_VLM_Groupe9.ipynb', as_version=4)
namespace = {'__name__': '__main__'}
# Les cellules sont repérées par leur première définition, indépendamment de leur numéro.
starts = ['# Copie du PDF fourni', 'from pathlib import Path\nfrom decimal import Decimal, InvalidOperation',
          'def sha256_file', '# Rectangles normalisés', 'def improve_contrast', 'COLUMNS =',
          'REFERENCE_TABLE =', 'records =', 'SYSTEM_ROLE =', 'def validate_page',
          'GEMINI_API_KEY =', 'def check_local_url', 'def local_map_schema', 'RUN_LOGS =',
          'def calculation_amount', 'def error_type', 'def degraded_images', 'def review_flagged']
for prefix in starts:
    candidates = [c for c in notebook.cells if c.cell_type=='code' and c.source.startswith(prefix)]
    if len(candidates)!=1:
        raise ValueError(f'Cellule ambiguë/absente : {prefix}')
    exec(compile(candidates[0].source, '<notebook:'+prefix.splitlines()[0]+'>', 'exec'), namespace)

namespace.update(RUN_API=True, API_IMAGES_REVIEWED=True, RUN_LOCAL=True, REPEATS=3)
namespace['local_diagnostic']()
campaign_id = 'verification_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
manifest = {'id':campaign_id, 'statut':'en_cours', 'repetitions':3, 'graine_ordre':42,
            'protocole':'Notebook Python, images 200 DPI masquées, température 0, zéro réessai de validation pour le benchmark.',
            'parallelisme':'Un essai local CPU et la série API distante se chevauchent ; les requêtes API restent séquentielles.',
            'experiences':[], 'erreurs':[]}
lock = threading.Lock()
manifest_path = ROOT/'outputs_vlm/campagne_courante.json'

def save():
    temporary = manifest_path.with_suffix('.tmp')
    temporary.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary.replace(manifest_path)

def run(backend, variant, label, images=None, pdf=None):
    result = namespace['run_document'](pdf or namespace['PDF_PATH'], images or namespace['IMAGES'],
                                       backend, variant, label=label, validation_retries=0)
    result['campaign_id'] = campaign_id
    namespace['dump_json'](Path(result['run_dir'])/'bilan.json',result)
    with lock:
        manifest['experiences'].append({'backend':backend,'variante':variant,'label':label,
            'run_dir':str(Path(result['run_dir']).relative_to(ROOT)), 'complet':result['document_complet']})
        save()
    print('TERMINE',backend,variant,label,f"{result['wall_seconds']:.2f} s",flush=True)
    return result

save()
with ThreadPoolExecutor(max_workers=1) as executor:
    local_future = executor.submit(run,'local','schema','local_verification')
    try:
        run('api','schema','principal_valide')
        rng=random.Random(42)
        for repeat in range(1,4):
            variants=namespace['VARIANTS'].copy();rng.shuffle(variants)
            for variant in variants:
                run('api',variant,f'ablation_validee_{repeat}')
        degraded=namespace['degraded_images'](namespace['IMAGES'])
        run('api','schema','scan_degrade_valide',images=degraded)
        # Deux entrées techniques, un seul bilan distinct. Pas de seconde entreprise inventée.
        synthetic=ROOT/'outputs_vlm/bilan_group9_scan_synthetique.pdf'
        with namespace['pymupdf'].open() as document:
            for image in degraded:
                document.new_page(width=595,height=842).insert_image(namespace['pymupdf'].Rect(0,0,595,842),filename=str(image))
            document.save(synthetic,garbage=4,deflate=True)
        batch=[]
        for index,(pdf,masks) in enumerate([(namespace['PDF_PATH'],namespace['MASKS_GROUP9']),(synthetic,{1:[],2:[]})],1):
            images=namespace['prepare_images'](pdf,ROOT/'outputs_vlm/batch_images'/f'verification_{index}',masks)
            result=run('api','schema','batch_valide',images=images,pdf=pdf)
            batch.append({'fichier':pdf.name,'complet':result['document_complet'],'run_dir':result['run_dir']})
        namespace['dump_json'](ROOT/'outputs_vlm/batch_manifest.json',batch)
    except Exception as error:
        with lock:
            manifest['erreurs'].append(str(error).replace(secret,'[clé masquée]')[:500]);save()
        print('Campagne API interrompue ; voir manifeste sans secret.',flush=True)
    try:
        local_future.result()
    except Exception as error:
        manifest['erreurs'].append(str(error).replace(secret,'[clé masquée]')[:500])
manifest['statut']='terminee' if not manifest['erreurs'] else 'terminee_avec_erreurs'
manifest['fin_utc']=datetime.now(timezone.utc).isoformat()
save()
os.environ.pop('GEMINI_API_KEY',None)
print('Campagne sauvegardée :',manifest_path.name,flush=True)
