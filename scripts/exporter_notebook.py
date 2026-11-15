"""Export HTML autonome pour relire toutes les sorties sans Jupyter."""
from pathlib import Path
import nbformat
from nbconvert import HTMLExporter
from traitlets.config import Config

root=Path(__file__).resolve().parent.parent
nb=nbformat.read(root/'TP_Extraction_Bilans_VLM_Groupe9.ipynb',as_version=4)
for cell in nb.cells:
    if cell.cell_type=='code' and cell.source.startswith('# Copie du PDF fourni'):
        cell.metadata.setdefault('tags',[]).append('donnees-integrees')
config=Config()
config.TagRemovePreprocessor.remove_input_tags={'donnees-integrees'}
config.HTMLExporter.embed_images=True
exporter=HTMLExporter(config=config,template_name='lab')
body,_=exporter.from_notebook_node(nb)
css='''<style>body{background:#f2f6f9}#notebook-container,main{max-width:1320px;margin:auto;background:white;padding:25px}.jp-RenderedHTMLCommon table{font-size:12px}.jp-RenderedHTMLCommon h1{color:#153a49}.jp-RenderedHTMLCommon h2{margin-top:32px;color:#176a60}.jp-OutputArea-output{overflow-x:auto}.vr-scroll{max-height:620px!important}pre{tab-size:4}summary:focus-visible{outline:2px solid #137d72}</style>'''
body=body.replace('</head>',css+'</head>')
destination=root/'TP_Extraction_Bilans_VLM_Groupe9.html'
destination.write_text(body,encoding='utf-8')
print('Export HTML autonome :',destination.name)
