'use client';
import {useState} from 'react';
import IconDownload from '@tabler/icons-react/icons/IconDownload';
import IconCode from '@tabler/icons-react/icons/IconCode';
import IconTable from '@tabler/icons-react/icons/IconTable';
import IconListCheck from '@tabler/icons-react/icons/IconListCheck';
import IconFileText from '@tabler/icons-react/icons/IconFileText';
import IconAlertTriangle from '@tabler/icons-react/icons/IconAlertTriangle';
import {accounting,evaluate,type MethodId,type PageAttempt,type Page} from '@/lib/engine';
import {duration,exportJson,money} from '@/lib/browser';
import reference from '@/lib/data/reference.json';

export type Run={id:MethodId;name:string;state:'queued'|'running'|'done'|'failed'|'cancelled'|'skipped';attempts:PageAttempt[];started:number|null;finished:number|null;error:string|null};
export function runFacts(run:Run,known:boolean){
  const pages=run.attempts.flatMap(a=>a.data?[a.data]:[]);const checks=accounting(pages);
  const score=known?evaluate(pages,reference as {lignes:Page['lignes']}):null;
  const ms=run.attempts.reduce((sum,a)=>sum+a.durationMs,0);
  const issues=checks.filter(c=>c.statut==='ecart').length;
  return {pages,checks,score,ms,issues,rows:pages.reduce((sum,p)=>sum+p.lignes.length,0)};
}

export default function ResultsPanel({run,known,file}:{run:Run;known:boolean;file:string}){
  const [tab,setTab]=useState('table');const [query,setQuery]=useState('');
  const facts=runFacts(run,known);
  const data={document:file,methode:run.id,source:'nouvelle_extraction_web',duree_requetes_ms:facts.ms,
    json_accepte:run.state==='done',controle:facts.checks,reference:known?facts.score:null,pages:run.attempts};
  const rows=facts.pages.flatMap(p=>p.lignes).filter(r=>`${r.poste} ${r.id}`.toLowerCase().includes(query.toLowerCase()));
  const tabs=[['table','Tableau',IconTable],['json','JSON',IconCode],['checks','Contrôles',IconListCheck],['raw','Réponse brute',IconFileText]] as const;
  return <section className="panel detail-panel" aria-label={'Résultat '+run.name}>
    <div className="section-heading"><div><span className="eyebrow">Résultat de la méthode</span><h2>{run.name}</h2></div>
      <button className="button secondary compact" onClick={()=>exportJson(data,`bilan-${run.id}.json`)}><IconDownload size={17}/>Exporter JSON</button></div>
    <div className="detail-metrics"><span><strong>{facts.rows}</strong> postes extraits</span><span><strong>{duration(facts.ms)}</strong> de requêtes</span>
      <span><strong>{facts.checks.filter(c=>c.statut==='ok').length}</strong> contrôles conformes</span>
      {facts.score?<span><strong>{facts.score.correct}/{facts.score.total}</strong> montants de référence</span>:<span>Exactitude <strong>non mesurée</strong></span>}</div>
    {run.error&&<p className="notice warning"><IconAlertTriangle size={18}/>{run.error}</p>}
    <div className="tabs" role="tablist" aria-label="Affichage du résultat">{tabs.map(([id,label,Icon])=><button key={id} role="tab" aria-selected={tab===id} className={tab===id?'active':''} onClick={()=>setTab(id)}><Icon size={17}/>{label}</button>)}</div>
    {tab==='table'&&<><div className="table-toolbar"><label>Rechercher un poste<input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Clients, immobilisations…"/></label>
      <span className="muted">Unité : {facts.pages[0]?.unite??'non confirmée'} · « — » = valeur absente</span></div>
      <div className="table-scroll"><table><thead><tr><th>Poste</th><th>Partie</th><th>Brut N</th><th>Amort. N</th><th>Net N</th><th>Net N−1</th></tr></thead>
        <tbody>{rows.map((r,i)=><tr key={r.id+'-'+i} className={r.type_ligne==='total'?'total-row':''}><td><small>{r.id}</small>{r.poste}</td><td>{r.rubrique}</td>
          {[r.montant_brut_N,r.montant_amort_N,r.montant_net_N,r.montant_net_N1].map((v,j)=><td key={j} className="numeric">{money(v)}</td>)}</tr>)}</tbody></table>
        {!rows.length&&<p className="empty-small">Aucun poste accepté. Consulter la réponse brute et les erreurs.</p>}</div></>}
    {tab==='json'&&<pre className="code-view">{JSON.stringify(data,null,2)}</pre>}
    {tab==='raw'&&<div className="raw-pages">{run.attempts.map(a=><details key={a.page} open={run.attempts.length===1}><summary>Page {a.page} · {a.ok?'acceptée':'rejetée'} · {duration(a.durationMs)}</summary>
      {a.error&&<p className="notice warning">{a.error}</p>}<pre className="code-view">{a.raw||'Aucune réponse complète reçue du fournisseur.'}</pre></details>)}</div>}
    {tab==='checks'&&<><p className="muted check-intro">Les cases vides valent zéro uniquement pour les sommes. Les valeurs illisibles rendent le contrôle indéterminé. Une égalité ne prouve pas une transcription exacte.</p>
      <div className="table-scroll"><table><thead><tr><th>Contrôle</th><th>Poste</th><th>Colonne</th><th>Écart</th><th>État</th></tr></thead><tbody>{facts.checks.map((c,i)=><tr key={i}><td>{c.controle}</td><td>{c.poste}</td><td>{c.colonne.replace('montant_','')}</td><td className="numeric">{money(c.ecart)}</td><td><span className={'badge '+(c.statut==='ok'?'success':c.statut==='ecart'?'danger':'neutral')}>{c.statut==='ok'?'Conforme':c.statut==='ecart'?'Écart':c.statut==='sans_donnees'?'Sans données':'Indéterminé'}</span></td></tr>)}</tbody></table></div></>}
  </section>;
}
