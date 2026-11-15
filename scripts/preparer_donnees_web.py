"""Prepare only anonymised examples and measured, sanitised data for the web app."""
from pathlib import Path
import hashlib
import json
import shutil
import pymupdf

root=Path(__file__).resolve().parent.parent
app=root/'webapp'
public=app/'public'
data=public/'data'
data.mkdir(parents=True,exist_ok=True)
out=root/'outputs_vlm'
read=lambda name:json.loads((out/name).read_text(encoding='utf-8-sig'))
history=read('resultats_finaux.json')
history=[{k:v for k,v in row.items() if k!='run_dir'} for row in history]
diag=read('diagnostic_local_brut.json')
main=read('bilan_group_9_extrait.json')
sample={'modele':main['modele'],'exercice':2024,'document_complet':True,'pages':main['pages']}
for name,obj in [('historique.json',{'experiences':history,'diagnostic_local':diag,'scope':{'bilans_reels':1,'pages':2,'postes':88,'montants':107,'date':'2026-11-15','experiences_archivees':len(list((out/'runs').glob('*/bilan.json')))}}),('extraction-exemple.json',sample),('catalogue.json',read('catalogue_sans_montants.json')),('reference.json',read('reference_annotee.json'))]:
    (data/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if name in ('catalogue.json','reference.json'):
        (app/'lib/data').mkdir(parents=True,exist_ok=True)
        (app/'lib/data'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=(out/'compte_rendu.md').read_text(encoding='utf-8')
(data/'compte-rendu.md').write_text(report.replace(str(root),'[projet local]'),encoding='utf-8')
pdf=public/'exemple-bilan.pdf'
with pymupdf.open() as doc:
    for index in (1,2):
        page=doc.new_page(width=595,height=842)
        page.insert_image(page.rect,filename=str(out/'images_group9'/f'page_{index:02d}.png'))
    doc.set_metadata({'title':'Bilan anonymise de demonstration','author':''})
    doc.save(pdf,garbage=4,deflate=True)
    assert all(not page.get_text().strip() for page in doc)
hashes=[hashlib.sha256(pdf.read_bytes()).hexdigest(),hashlib.sha256((root/'bilan_group_9.pdf').read_bytes()).hexdigest()]
(data/'exemple.json').write_text(json.dumps({'hashes':hashes,'name':'Bilan du groupe 9, exemple anonymisé','pages':2,'unit':'inconnue'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
design=app/'design'
design.mkdir(exist_ok=True)
source=Path('C:/Users/SetupGame/.codex/generated_images/01a1dba1-6681-7693-94b2-cfd9304b602d/exec-e3b806e2-018a-4389-9135-ab28680fe787.png')
if source.exists(): shutil.copy2(source,design/'reference-comparaison.png')
print('Sanitised history and raster-only example PDF prepared.')
