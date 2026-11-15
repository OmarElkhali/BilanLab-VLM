'use client';
import {useEffect,useRef,useState,type DragEvent,type PointerEvent} from 'react';
import IconChartBar from '@tabler/icons-react/icons/IconChartBar';
import IconScale from '@tabler/icons-react/icons/IconScale';
import IconSitemap from '@tabler/icons-react/icons/IconSitemap';
import IconBook2 from '@tabler/icons-react/icons/IconBook2';
import IconSettings from '@tabler/icons-react/icons/IconSettings';
import IconUpload from '@tabler/icons-react/icons/IconUpload';
import IconFileDescription from '@tabler/icons-react/icons/IconFileDescription';
import IconPlayerPlay from '@tabler/icons-react/icons/IconPlayerPlay';
import IconPlayerStop from '@tabler/icons-react/icons/IconPlayerStop';
import IconDownload from '@tabler/icons-react/icons/IconDownload';
import IconX from '@tabler/icons-react/icons/IconX';
import IconCheck from '@tabler/icons-react/icons/IconCheck';
import IconAlertTriangle from '@tabler/icons-react/icons/IconAlertTriangle';
import IconChevronLeft from '@tabler/icons-react/icons/IconChevronLeft';
import IconChevronRight from '@tabler/icons-react/icons/IconChevronRight';
import IconMaximize from '@tabler/icons-react/icons/IconMaximize';
import IconEyeOff from '@tabler/icons-react/icons/IconEyeOff';
import IconEraser from '@tabler/icons-react/icons/IconEraser';
import IconPlus from '@tabler/icons-react/icons/IconPlus';
import IconArrowUpRight from '@tabler/icons-react/icons/IconArrowUpRight';
import IconClock from '@tabler/icons-react/icons/IconClock';
import IconLoader2 from '@tabler/icons-react/icons/IconLoader2';
import IconInfoCircle from '@tabler/icons-react/icons/IconInfoCircle';
import {METHODS,type MethodId,type PageAttempt} from '@/lib/engine';
import {prepareFiles,preparedImage,exportJson,duration,type PreparedPage,type Mask} from '@/lib/browser';
import ResultsPanel,{runFacts,type Run} from './ResultsPanel';
import {HistoryView,ArchitectureView,ProjectView,type History} from './ProjectViews';

type View='compare'|'history'|'architecture'|'project';
type Status={local:boolean;ollamaAvailable:boolean;localModels:string[]};
const navigation=[{id:'compare',name:'Comparer',Icon:IconScale},{id:'history',name:'Résultats du TP',Icon:IconChartBar},{id:'architecture',name:'Architecture',Icon:IconSitemap},{id:'project',name:'Le projet',Icon:IconBook2}] as const;

export default function Laboratory(){
  const [view,setView]=useState<View>('compare');const [status,setStatus]=useState<Status>({local:false,ollamaAvailable:false,localModels:[]});
  const [history,setHistory]=useState<History|null>(null);const [knownHashes,setKnownHashes]=useState<string[]>([]);
  const [config,setConfig]=useState({apiKey:'',apiModel:'gemini-3.1-flash-lite',localModel:'qwen3-vl:4b-instruct'});const [settings,setSettings]=useState(false);
  const [pages,setPages]=useState<PreparedPage[]>([]);const [pageIndex,setPageIndex]=useState(0);const [fileName,setFileName]=useState('');
  const [fileHash,setFileHash]=useState('');const [preparationMs,setPreparationMs]=useState(0);const [loading,setLoading]=useState(false);
  const [selected,setSelected]=useState<MethodId[]>(['baseline','role','constraints','fewshot','json_mode','schema']);
  const [consent,setConsent]=useState(false);const [dragging,setDragging]=useState(false);const [drawing,setDrawing]=useState(false);
  const [draft,setDraft]=useState<Mask|null>(null);const [zoom,setZoom]=useState(false);const [error,setError]=useState('');
  const [runs,setRuns]=useState<Run[]>([]);const [activeResult,setActiveResult]=useState<MethodId|null>(null);const [busy,setBusy]=useState(false);const [tick,setTick]=useState(0);
  const fileInput=useRef<HTMLInputElement>(null);const abort=useRef<AbortController|null>(null);const uploadVersion=useRef(0);
  const settingsDialog=useRef<HTMLDialogElement>(null);const zoomDialog=useRef<HTMLDialogElement>(null);const pointerStart=useRef<{x:number;y:number}|null>(null);
  const current=pages[pageIndex];const known=!!fileHash&&knownHashes.includes(fileHash);const chosenResult=runs.find(r=>r.id===activeResult);

  useEffect(()=>{
    const control=new AbortController();
    fetch('/api/status',{signal:control.signal}).then(async r=>await r.json() as Status).then(data=>{setStatus(data);if(data.ollamaAvailable)setSelected(METHODS.map(m=>m.id));}).catch(()=>{});
    fetch('/data/historique.json',{signal:control.signal}).then(async r=>await r.json() as History).then(setHistory).catch(()=>{});
    fetch('/data/exemple.json',{signal:control.signal}).then(async r=>await r.json() as {hashes:string[]}).then(d=>setKnownHashes(d.hashes)).catch(()=>{});
    const hash=window.location.hash.slice(1);if(navigation.some(n=>n.id===hash))setView(hash as View);
    return()=>{control.abort();abort.current?.abort();};
  },[]);
  useEffect(()=>{if(!busy)return;const interval=setInterval(()=>setTick(Date.now()),250);return()=>clearInterval(interval);},[busy]);
  useEffect(()=>{if(settings)settingsDialog.current?.showModal();else settingsDialog.current?.close();},[settings]);
  useEffect(()=>{if(zoom)zoomDialog.current?.showModal();else zoomDialog.current?.close();},[zoom]);
  function go(next:View){setView(next);window.history.replaceState(null,'','#'+next);window.scrollTo({top:0});}

  async function load(files:File[]){
    if(busy)return;const version=++uploadVersion.current;const start=performance.now();setLoading(true);setError('');setConsent(false);setRuns([]);setActiveResult(null);
    try{const prepared=await prepareFiles(files);if(version!==uploadVersion.current)return;setPages(prepared.pages);setPageIndex(0);setFileName(prepared.name);setFileHash(prepared.hash);setPreparationMs(performance.now()-start);}
    catch(e){if(version===uploadVersion.current){setPages([]);setError(e instanceof Error?e.message:'Lecture du document impossible.');}}
    finally{if(version===uploadVersion.current)setLoading(false);}
  }
  async function example(){
    if(busy||loading)return;setError('');
    try{const response=await fetch('/exemple-bilan.pdf');if(!response.ok)throw new Error('Exemple indisponible.');const blob=await response.blob();await load([new File([blob],'exemple-bilan-anonymise.pdf',{type:'application/pdf'})]);}
    catch(e){setError(e instanceof Error?e.message:'Exemple indisponible.');}
  }
  function drop(event:DragEvent){event.preventDefault();setDragging(false);if(!busy&&!loading)void load(Array.from(event.dataTransfer.files));}
  function toggle(id:MethodId){if(!busy)setSelected(current=>current.includes(id)?current.filter(v=>v!==id):[...current,id]);}
  function changeMasks(masks:Mask[]){setPages(old=>old.map((p,i)=>i===pageIndex?{...p,masks}:p));setConsent(false);}
  function point(event:PointerEvent<HTMLDivElement>){const rect=event.currentTarget.getBoundingClientRect();return {x:Math.max(0,Math.min(1,(event.clientX-rect.left)/rect.width)),y:Math.max(0,Math.min(1,(event.clientY-rect.top)/rect.height))};}
  function startMask(event:PointerEvent<HTMLDivElement>){if(!drawing||busy)return;event.preventDefault();event.currentTarget.setPointerCapture(event.pointerId);pointerStart.current=point(event);setDraft({...pointerStart.current,w:0,h:0});}
  function moveMask(event:PointerEvent<HTMLDivElement>){if(!pointerStart.current||!drawing)return;const to=point(event),from=pointerStart.current;setDraft({x:Math.min(from.x,to.x),y:Math.min(from.y,to.y),w:Math.abs(from.x-to.x),h:Math.abs(from.y-to.y)});}
  function endMask(){if(draft&&draft.w>.005&&draft.h>.005)changeMasks([...current.masks,draft]);pointerStart.current=null;setDraft(null);setDrawing(false);}
  function update(id:MethodId,patch:Partial<Run>){setRuns(old=>old.map(r=>r.id===id?{...r,...patch}:r));}

  async function run(){
    setError('');
    if(!pages.length){setError('Déposer un bilan pour commencer.');fileInput.current?.focus();return;}
    if(!consent){setError('Vérifier les pages et cocher l’autorisation de traitement.');return;}
    if(!selected.length){setError('Sélectionner au moins une méthode.');return;}
    if(selected.some(id=>id!=='local')&&!config.apiKey.trim()){setError('Ajouter une clé Gemini dans Configuration pour les méthodes API.');setSettings(true);return;}
    const chosen=METHODS.filter(m=>selected.includes(m.id));const controller=new AbortController();abort.current=controller;
    setRuns(chosen.map(m=>({id:m.id,name:m.name,state:'queued',attempts:[],started:null,finished:null,error:null})));setBusy(true);setActiveResult(chosen[0].id);let blockedApi=false;
    try{
      for(const method of chosen){
        if(controller.signal.aborted)break;
        if(method.provider==='api'&&blockedApi){update(method.id,{state:'skipped',error:'Non lancé : l’accès API ou le quota doit être corrigé.'});continue;}
        update(method.id,{state:'running',started:Date.now()});const attempts:PageAttempt[]=[];
        try{
          for(let i=0;i<pages.length;i++){
            if(controller.signal.aborted)throw new DOMException('Annulé','AbortError');
            const image=await preparedImage(pages[i],method.id==='local');
            const response=await fetch('/api/extract',{method:'POST',headers:{'content-type':'application/json'},signal:controller.signal,
              body:JSON.stringify({method:method.id,image,page:i+1,apiKey:config.apiKey,apiModel:config.apiModel,localModel:config.localModel,knownExample:known,consent:true})});
            const result=await response.json() as PageAttempt;if(!response.ok)throw new Error(result.error??'Traitement impossible.');
            attempts.push(result as PageAttempt);update(method.id,{attempts:[...attempts]});
            if(method.provider==='api'&&result.httpStatus!==null&&[401,403,429].includes(result.httpStatus)){blockedApi=true;break;}
          }
          const ok=attempts.length===pages.length&&attempts.every(a=>a.ok);
          update(method.id,{state:ok?'done':'failed',finished:Date.now(),attempts:[...attempts],error:ok?null:attempts.find(a=>a.error)?.error??'Une page n’a pas été acceptée.'});
        }catch(e){
          if(controller.signal.aborted){update(method.id,{state:'cancelled',finished:Date.now(),attempts:[...attempts],error:'Traitement annulé.'});break;}
          update(method.id,{state:'failed',finished:Date.now(),attempts:[...attempts],error:e instanceof Error?e.message:'Erreur de traitement.'});
        }
      }
    }finally{if(controller.signal.aborted)setRuns(old=>old.map(r=>r.state==='queued'||r.state==='running'?{...r,state:'cancelled',error:'Traitement annulé.'}:r));setBusy(false);abort.current=null;}
  }
  function exportAll(){exportJson({document:fileName,source_sha256:fileHash,source:'nouvelle_extraction_web',preparation_ms:preparationMs,reference_disponible:known,resultats:runs.map(r=>({methode:r.id,etat:r.state,reponses:r.attempts,...runFacts(r,known)}))},'comparaison-bilan.json');}
  const finished=runs.filter(r=>!['queued','running'].includes(r.state)).length;
  const completed=runs.filter(r=>r.state==='done');const fastest=completed.length?Math.min(...completed.map(r=>runFacts(r,known).ms)):null;

  return <div className="app-shell">
    <aside className="sidebar"><a href="#compare" className="brand" onClick={e=>{e.preventDefault();go('compare');}}><span className="brand-mark"><IconChartBar size={28} stroke={2.2}/></span><span>BilanLab<small>Laboratoire VLM</small></span></a>
      <nav aria-label="Navigation principale">{navigation.map(({id,name,Icon})=><a href={'#'+id} aria-label={name} key={id} className={'nav-item '+(view===id?'active':'')} aria-current={view===id?'page':undefined} onClick={e=>{e.preventDefault();go(id);}}><Icon size={21}/><span>{name}</span></a>)}</nav>
      <div className="sidebar-bottom"><div className="project-signature">Transformers et LLMs<small>ENSAM Casablanca · Groupe 9</small></div><button className="nav-item" onClick={()=>setSettings(true)}><IconSettings size={20}/><span>Configuration</span></button></div></aside>
    <div className="main-shell"><header className="topbar"><div className="breadcrumb">Laboratoire <span>/</span> <strong>{navigation.find(n=>n.id===view)?.name}</strong></div>
      <div className="top-actions"><span className={'service-state '+(status.ollamaAvailable?'available':'')}><span/>{status.ollamaAvailable?'Ollama disponible':status.local?'Ollama non connecté':'Espace privé'}</span><button className="button secondary compact" onClick={()=>setSettings(true)}><IconSettings size={17}/><span>Configuration</span></button></div></header>
    <main className="main-content">
      {view==='history'&&<HistoryView data={history}/>}{view==='architecture'&&<ArchitectureView/>}{view==='project'&&<ProjectView/>}
      {view==='compare'&&<>
        <div className="page-heading"><div><span className="eyebrow">Extraction de bilans marocains</span><h1>Comparer les méthodes.</h1><p>Déposez un bilan, mesurez chaque extraction et vérifiez les résultats.</p></div><button className="text-link" onClick={()=>go('history')}>Voir les essais du TP <IconArrowUpRight size={17}/></button></div>
        {error&&<div className="notice warning" role="alert"><IconAlertTriangle size={19}/><span>{error}</span><button aria-label="Fermer le message" onClick={()=>setError('')}><IconX size={17}/></button></div>}
        <div className="workspace-grid"><section className="document-column" aria-label="Document à analyser">
          <input ref={fileInput} className="visually-hidden" type="file" accept=".pdf,image/png,image/jpeg,image/webp" multiple disabled={busy||loading} aria-label="Choisir le bilan" onChange={e=>{void load(Array.from(e.target.files??[]));e.target.value='';}}/>
          {!pages.length?<div className={'dropzone '+(dragging?'dragging':'')} onDragOver={e=>{e.preventDefault();setDragging(true);}} onDragLeave={()=>setDragging(false)} onDrop={drop}>
            <div className="document-symbol">{loading?<IconLoader2 className="spin" size={36}/>:<IconFileDescription size={38} stroke={1.4}/>}</div><h2>{loading?'Préparation des pages…':'Déposez votre bilan'}</h2><p>PDF ou images · jusqu’à 8 pages</p>
            <button className="button primary" disabled={loading||busy} onClick={()=>fileInput.current?.click()}><IconUpload size={18}/>Choisir un fichier</button><button className="button secondary" disabled={loading||busy} onClick={()=>void example()}>Exemple anonymisé</button><span className="upload-note">Modèle normal actif / passif · 20 Mo par fichier</span></div>:
          <section className="panel document-panel"><div className="document-header"><div><IconFileDescription size={20}/><strong title={fileName}>{fileName}</strong></div><button className="icon-button" aria-label="Changer de document" disabled={busy||loading} onClick={()=>fileInput.current?.click()}><IconUpload size={18}/></button></div>
            <div className="document-pages"><button className="icon-button" disabled={pageIndex===0||busy} aria-label="Page précédente" onClick={()=>setPageIndex(i=>i-1)}><IconChevronLeft size={18}/></button><span>{current.name} <small>{pageIndex+1}/{pages.length}</small></span><button className="icon-button" disabled={pageIndex===pages.length-1||busy} aria-label="Page suivante" onClick={()=>setPageIndex(i=>i+1)}><IconChevronRight size={18}/></button><button className="icon-button" aria-label="Agrandir la page" onClick={()=>setZoom(true)}><IconMaximize size={17}/></button></div>
            <div className="preview-background"><div className={'page-image '+(drawing?'drawing':'')} onPointerDown={startMask} onPointerMove={moveMask} onPointerUp={endMask} onPointerCancel={()=>{pointerStart.current=null;setDraft(null);}}>
              <img src={current.src} alt={'Aperçu de '+current.name} draggable={false}/>{[...current.masks,...(draft?[draft]:[])].map((mask,i)=><span key={i} className={'mask '+(i===current.masks.length?'draft':'')} style={{left:mask.x*100+'%',top:mask.y*100+'%',width:mask.w*100+'%',height:mask.h*100+'%'}}/>)}</div></div>
            <div className="mask-tools"><button className="button secondary compact" disabled={busy} onClick={()=>changeMasks([...current.masks,{x:0,y:0,w:.42,h:.095}])}><IconEyeOff size={16}/>Masquer l’entête</button><button className={'icon-button '+(drawing?'selected':'')} disabled={busy} title="Dessiner un masque sur la page" aria-label="Dessiner un masque" aria-pressed={drawing} onClick={()=>setDrawing(!drawing)}><IconPlus size={18}/></button><button className="icon-button" disabled={busy||!current.masks.length} aria-label="Effacer les masques de cette page" onClick={()=>changeMasks([])}><IconEraser size={18}/></button></div><p className="table-note">Vérifiez chaque page et masquez les informations sensibles. Le zoom permet de lire les chiffres.</p></section>}
          <p className="document-privacy"><IconInfoCircle size={17}/>Le document reste dans le navigateur pendant sa préparation. Seules les images préparées sont envoyées lors du lancement.</p>
        </section>
        <section className="panel methods-panel"><div className="section-heading"><div><h2>Méthodes à comparer</h2><p className="muted">Le même document, des stratégies différentes.</p></div><button className="text-link small" disabled={busy} onClick={()=>setSelected(METHODS.filter(m=>m.provider==='api'||status.ollamaAvailable).map(m=>m.id))}>Tout sélectionner</button></div>
          <div className="method-list">{METHODS.map(method=>{const unavailable=method.provider==='local'&&!status.ollamaAvailable;
            return <label className={'method-row '+(unavailable?'unavailable':'')} key={method.id}><input type="checkbox" checked={selected.includes(method.id)} disabled={busy||unavailable} onChange={()=>toggle(method.id)}/><span className="method-text"><strong>{method.name}</strong><small>{unavailable?(status.local?'Démarrer Ollama sur ce PC pour activer cette méthode.':'Disponible dans la version locale sur votre PC.'):method.description}</small></span><span className={'provider '+(method.provider==='local'?'local':'')}>{method.provider==='local'?'Local':'API'}</span></label>;})}</div>
          <div className="launch-area"><label className="consent"><input type="checkbox" checked={consent} disabled={busy||!pages.length} onChange={e=>setConsent(e.target.checked)}/><span>J’ai vérifié les pages préparées et j’autorise leur traitement par les méthodes choisies.</span></label>
            {busy?<button className="button stop full" onClick={()=>abort.current?.abort()}><IconPlayerStop size={19}/>Annuler la comparaison</button>:<button className="button primary full" disabled={loading} onClick={()=>void run()}><IconPlayerPlay size={19}/>Lancer la comparaison <span>{selected.length} méthodes</span></button>}
            <div className="launch-meta"><span>{pages.length?`${pages.length} page${pages.length>1?'s':''} · ${selected.length*pages.length} requêtes au maximum`:'Choisissez votre document pour commencer.'}</span><span>{config.apiKey?'Clé API renseignée':'Clé API à configurer'}</span></div></div>
        </section></div>
        <section className="panel comparison-panel"><div className="section-heading"><div><h2>Résultats de la comparaison</h2><p className="muted">{busy?`${finished}/${runs.length} méthodes terminées. Les durées en cours sont affichées en direct.`:'Mesures de cette analyse, sans reprise des scores historiques.'}</p></div>{!!runs.length&&<button className="button secondary compact" onClick={exportAll}><IconDownload size={17}/>Tout exporter</button>}</div>
          {!runs.length?<div className="empty-state"><IconFileDescription size={30} stroke={1.3}/><h3>Prêt pour votre premier bilan</h3><p>Importez un document et choisissez les méthodes.<br/>Les résultats apparaîtront ici, sans mesure simulée.</p></div>:<>
            <div className="run-summary"><span><IconClock size={17}/>Préparation : {duration(preparationMs)}</span><span>{finished}/{runs.length} méthodes terminées</span>{fastest!==null&&<span>Plus courte extraction acceptée : <strong>{duration(fastest)}</strong></span>}{known?<span className="badge success">Référence de l’exemple disponible</span>:<span className="badge neutral">Document sans référence annotée</span>}</div>
            <div className="table-scroll"><table className="comparison-table"><thead><tr><th>Méthode</th><th>État</th><th>Durée des requêtes</th><th>JSON</th><th>Contrôles</th><th>Exactitude</th><th/></tr></thead><tbody>{runs.map(r=>{
              const facts=runFacts(r,known);const running=r.state==='running';const elapsed=running&&r.started?Math.max(0,(tick||Date.now())-r.started):facts.ms;
              const label=running?`Page ${Math.min(r.attempts.length+1,pages.length)}/${pages.length}`:r.state==='queued'?'En attente':r.state==='done'?(facts.issues?'À vérifier':'Terminé'):r.state==='cancelled'?'Annulé':r.state==='skipped'?'Non lancé':'Rejeté';
              return <tr key={r.id} className={activeResult===r.id?'selected-row':''}><td><strong>{r.name}</strong><small>{r.attempts[0]?.model??(r.id==='local'?config.localModel:config.apiModel)}</small></td><td><span className={'badge '+(r.state==='done'&&!facts.issues?'success':r.state==='failed'||facts.issues?'warning':'neutral')}>{running&&<IconLoader2 size={13} className="spin"/>}{label}</span></td><td className="numeric">{r.state==='queued'||r.state==='skipped'?'—':duration(elapsed)}{running&&<small>en cours</small>}</td><td>{r.attempts.length?`${r.attempts.filter(a=>a.jsonValid).length}/${pages.length} syntaxe valide`:'—'}</td><td>{facts.pages.length?`${facts.checks.filter(c=>c.statut==='ok').length} conformes${facts.issues?', '+facts.issues+' écarts':''}`:'—'}</td><td>{known&&r.attempts.length?`${facts.score?.correct}/${facts.score?.total}`:'Non mesurée'}</td><td><button className="text-link" onClick={()=>setActiveResult(r.id)} aria-label={'Afficher '+r.name}>Détails <IconArrowUpRight size={16}/></button></td></tr>;})}</tbody></table></div></>}
        </section>{chosenResult&&<ResultsPanel key={chosenResult.id} run={chosenResult} known={known} file={fileName}/>}
      </>}
      <footer className="app-footer"><span>BilanLab · Extraction et validation documentaire</span><button className="text-link" onClick={()=>go('project')}>Périmètre et limites <IconArrowUpRight size={14}/></button></footer>
    </main></div>
    <dialog ref={settingsDialog} className="settings-dialog" onCancel={()=>setSettings(false)}><div className="dialog-header"><h2>Configuration des modèles</h2><button className="icon-button" aria-label="Fermer la configuration" onClick={()=>setSettings(false)}><IconX size={20}/></button></div><p>La clé est conservée uniquement en mémoire pour cette session. Elle ne figure pas dans les exports.</p>
      <form onSubmit={e=>{e.preventDefault();setSettings(false);}}><label>Clé Gemini API<input type="password" value={config.apiKey} onChange={e=>setConfig(c=>({...c,apiKey:e.target.value}))} placeholder="Votre clé API" autoComplete="off" autoFocus/></label><label>Modèle API<input value={config.apiModel} onChange={e=>setConfig(c=>({...c,apiModel:e.target.value}))} required pattern="[A-Za-z0-9._-]+"/></label><label>Modèle Ollama<input value={config.localModel} onChange={e=>setConfig(c=>({...c,localModel:e.target.value}))} list="local-models" required/><datalist id="local-models">{status.localModels.map(m=><option key={m} value={m}/>)}</datalist></label>
        <p className="notice"><IconInfoCircle size={17}/>{status.local?'Ollama doit être lancé sur ce PC. Les modèles cloud sont exclus du mode local.':'Sur le site hébergé, utiliser Gemini. Pour Qwen, démarrer la version locale sur le PC avec Ollama.'}</p><button className="button primary full" type="submit"><IconCheck size={18}/>Utiliser cette configuration</button></form></dialog>
    <dialog ref={zoomDialog} className="zoom-dialog" onCancel={()=>setZoom(false)}><div className="dialog-header"><h2>{current?.name}</h2><button className="icon-button" aria-label="Fermer le zoom" onClick={()=>setZoom(false)}><IconX size={20}/></button></div>{current&&<div className="zoom-scroll"><div className="page-image"><img src={current.src} alt="Page agrandie pour vérification"/>{current.masks.map((mask,i)=><span key={i} className="mask" style={{left:mask.x*100+'%',top:mask.y*100+'%',width:mask.w*100+'%',height:mask.h*100+'%'}}/>)}</div></div>}</dialog>
  </div>;
}
