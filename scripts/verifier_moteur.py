"""Autocontrôle ciblé : JSON, montants, évaluation et relecture d'une page rejetée."""
import copy
from pathlib import Path
import os
import sys
import nbformat

sys.stdout.reconfigure(encoding='utf-8')

root=Path(__file__).resolve().parent.parent
os.chdir(root)
nb=nbformat.read(root/'TP_Extraction_Bilans_VLM_Groupe9.ipynb',as_version=4)
ns={'__name__':'__main__'}
prefixes=['# Copie du PDF fourni','from pathlib import Path\nfrom decimal import Decimal, InvalidOperation',
    'def sha256_file','COLUMNS =','REFERENCE_TABLE =','records =','SYSTEM_ROLE =','def validate_page',
    'RUN_LOGS =','def calculation_amount','def ref_amount','def reference_document','def error_type','def review_flagged']
for prefix in prefixes:
    cell=next(c for c in nb.cells if c.cell_type=='code' and c.source.startswith(prefix))
    exec(compile(cell.source,'<notebook-test>','exec'),ns)
for invalid in ['{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}','```json\n{}\n```']:
    try:ns['strict_json'](invalid)
    except ValueError:pass
    else:raise AssertionError('JSON invalide accepté')
assert all(not any(col in row for col in ns['COLUMNS']) for row in ns['CATALOGUE'])
reference=ns['reference_document']()
reference['source_sha256']=ns['REFERENCE_SOURCE_SHA256']
metrics,errors=ns['evaluate'](reference)
assert metrics['numeric_correct']==metrics['numeric_total']==107 and not errors
bad=copy.deepcopy(reference['pages'][0]);bad['lignes'].append(bad['lignes'][0])
try:ns['validate_page']({k:v for k,v in bad.items() if k!='page'})
except ValueError:pass
else:raise AssertionError('Poste dupliqué accepté')

# Simuler uniquement le transport pour vérifier le défaut de relecture sans appel au modèle.
calls=[]
def stub(image_path,variant,correction=''):
    calls.append(image_path)
    nature=ns['page_hint'](image_path)
    lines=[]
    for row in ns['REFERENCE']:
        if row['rubrique']!=nature:continue
        values=[row[c] if row['etats'][c]=='lu' else 'NA' if row['etats'][c]=='non_applicable' else None for c in ns['COLUMNS']]
        lines.append({'id':row['id'],'valeurs':values})
    data={'nature':nature,'exercice_N':2024,'unite':'inconnue','preuve_unite':'','lignes':lines,'avertissements':[]}
    return {'text':ns['json'].dumps(data),'finish_reason':'STOP','seconds':0.0}
ns.update(call_gemini=stub,call_ollama=stub)
folder=root/'outputs_vlm/tests_techniques';folder.mkdir(exist_ok=True)
result={'backend':'api','document_complet':False,'pages':[],'run_dir':str(folder)}
proposals=ns['review_flagged'](result,[Path('page_01.png'),Path('page_02.png')])
assert len(calls)==2 and len(proposals)==2 and all('proposition' in p for p in proposals)
assert result['pages']==[], 'La relecture a modifié les résultats initiaux'
print('OK : contrôles techniques ciblés, aucune inférence ni mesure de performance synthétique.')
