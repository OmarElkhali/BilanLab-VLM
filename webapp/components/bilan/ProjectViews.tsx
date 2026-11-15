'use client';
import {useState} from 'react';
import IconFileTypePdf from '@tabler/icons-react/icons/IconFileTypePdf';
import IconPhoto from '@tabler/icons-react/icons/IconPhoto';
import IconAdjustments from '@tabler/icons-react/icons/IconAdjustments';
import IconBraces from '@tabler/icons-react/icons/IconBraces';
import IconShieldCheck from '@tabler/icons-react/icons/IconShieldCheck';
import IconChartBar from '@tabler/icons-react/icons/IconChartBar';
import IconArrowRight from '@tabler/icons-react/icons/IconArrowRight';
import IconDownload from '@tabler/icons-react/icons/IconDownload';
import IconBook2 from '@tabler/icons-react/icons/IconBook2';
import IconCode from '@tabler/icons-react/icons/IconCode';
import IconFolder from '@tabler/icons-react/icons/IconFolder';
import IconCpu from '@tabler/icons-react/icons/IconCpu';
import IconCloud from '@tabler/icons-react/icons/IconCloud';
import IconInfoCircle from '@tabler/icons-react/icons/IconInfoCircle';
import {duration,exportJson} from '@/lib/browser';

type Experience={backend:string;modele:string;variante:string;experience:string;document_complet:boolean;numeric_correct:number;numeric_total:number;latence_s:number;controles_ok:number;controles_ecart:number;completude_lignes:number};
export type History={experiences:Experience[];diagnostic_local:{montants_bruts_corrects:number;montants_attendus:number;marqueurs_NA_incompatibles:number;annees_brutes:number[]};scope:{bilans_reels:number;pages:number;postes:number;montants:number;date:string}};
const names:Record<string,string>={baseline:'Consigne simple',role:'Rôle système',constraints:'Contraintes',fewshot:'Exemple fictif',json_mode:'Mode JSON',schema:'Schéma contraint'};
export function HistoryView({data}:{data:History|null}){
  if(!data)return <section className="panel empty-state">Chargement des résultats enregistrés…</section>;
  const main=data.experiences.find(r=>r.experience==='principal_relecture')??data.experiences.find(r=>r.experience==='principal_valide')!;
  const local=data.experiences.find(r=>r.backend==='local')!;
  const study=['baseline','role','constraints','fewshot','json_mode','schema'].map(id=>{
    const trials=data.experiences.filter(r=>r.experience.startsWith('ablation_validee_')&&r.variante===id);
    const times=trials.map(r=>r.latence_s).sort((a,b)=>a-b);const middle=Math.floor(times.length/2);
    return {...trials[0],trials:trials.length,accepted:trials.filter(r=>r.document_complet).length,
      numeric_correct:trials.reduce((sum,r)=>sum+r.numeric_correct,0)/trials.length,
      latence_s:times.length%2?times[middle]:(times[middle-1]+times[middle])/2};
  });
  const max=Math.max(...study.map(r=>r.latence_s));
  return <><div className="page-heading"><div><span className="eyebrow">Mesures du notebook</span><h1>Les résultats du projet</h1><p>Des expériences enregistrées, distinctes de vos nouvelles analyses.</p></div><span className="badge neutral">15 novembre 2026</span></div>
    <section className="historical-summary"><div className="summary-main"><span className="eyebrow">Solution retenue sur le bilan fourni</span><h2>Gemini retrouve les 107 montants.</h2><p>Le JSON extrait correspond à la référence de travail, puis passe les contrôles comptables.</p><a className="text-link" href="/data/extraction-exemple.json" download>Télécharger le JSON de l’exemple <IconDownload size={16}/></a></div>
      <div className="stat-stack"><div><strong>{main.numeric_correct}/{main.numeric_total}</strong><span>montants strictement exacts</span></div><div><strong>{main.controles_ok}</strong><span>contrôles conformes</span></div><div><strong>{duration(main.latence_s*1000)}</strong><span>pour les deux pages</span></div></div></section>
    <p className="notice"><IconInfoCircle size={18}/>Un seul bilan réel, utilisé aussi pour ajuster les prompts. Les 88 postes et 107 cellules annotées ne constituent pas un test indépendant.</p>
    <div className="history-grid"><section className="panel"><div className="section-heading"><h2>Comparer les prompts</h2><span className="muted">Trois répétitions par variante</span></div>
      <div className="table-scroll"><table><thead><tr><th>Méthode API</th><th>Montants moyens</th><th>Durée médiane</th><th>Documents complets</th></tr></thead><tbody>{study.map(r=><tr key={r.variante}><td>{names[r.variante]}</td><td className="numeric">{r.numeric_correct.toLocaleString('fr-FR',{maximumFractionDigits:1})}/{r.numeric_total}</td><td className="numeric">{duration(r.latence_s*1000)}</td><td><span className={'badge '+(r.accepted===r.trials?'success':'warning')}>{r.accepted}/{r.trials}</span></td></tr>)}</tbody></table></div>
      <p className="table-note">La baseline ajoute des clôtures Markdown. Son score nul correspond au rejet du JSON, pas nécessairement à une absence de lecture des chiffres.</p></section>
      <section className="panel"><div className="section-heading"><h2>Durée médiane des méthodes</h2></div><div className="duration-chart">{study.map(r=><div className="chart-row" key={r.variante}><span>{names[r.variante]}</span><div className="bar-area"><span className="chart-bar" style={{width:`${r.latence_s/max*100}%`}}/></div><strong>{r.latence_s.toLocaleString('fr-FR',{maximumFractionDigits:2})} s</strong></div>)}</div>
      <p className="table-note">Le réseau et le service font varier la latence. Ces essais ne permettent pas de classer les méthodes avec certitude.</p></section></div>
    <section className="panel local-study"><div><span className="eyebrow">Ollama sur CPU</span><h2>Une extraction locale mesurée, mais rejetée.</h2><p>{data.diagnostic_local.montants_bruts_corrects}/{data.diagnostic_local.montants_attendus} valeurs brutes sont correctes. Les marqueurs non applicables, les décalages de lignes et une année mal lue empêchent d’accepter le résultat.</p></div>
      <div className="local-stat"><strong>{duration(local.latence_s*1000)}</strong><span>Deux pages · Qwen3-VL 4B Instruct</span><span className="badge warning">0 montant accepté par le pipeline strict</span></div></section>
    <section className="panel"><h2>Robustesse et périmètre</h2><p>Le scan synthétique dégradé conserve 107/107 montants exacts avec l’API. La file de traitement a réussi sur deux fichiers : l’original et sa version synthétique. Ils représentent un seul bilan distinct.</p><a className="button secondary compact" href="/data/compte-rendu.md" download><IconDownload size={17}/>Compte-rendu complet</a></section>
  </>;
}

const steps=[
  {title:'Document',Icon:IconFileTypePdf,body:'Un PDF ou des images du bilan marocain. Le navigateur vérifie les formats et prépare les pages.',path:'lib/browser.ts · prepareFiles'},
  {title:'Préparation',Icon:IconPhoto,body:'PDF.js rend les pages en images. Des masques visuels sont appliqués avant l’envoi. La couche texte du PDF n’est pas transmise.',path:'Canvas · PDF.js · masques utilisateur'},
  {title:'Méthodes',Icon:IconAdjustments,body:'Six variantes Gemini et une méthode Qwen via Ollama. Les prompts ne contiennent pas les montants de la référence.',path:'lib/engine.ts · promptFor / runPage'},
  {title:'JSON',Icon:IconBraces,body:'Le parsing rejette les clôtures Markdown et les clés dupliquées. Le contrat décrit les postes, les colonnes, les états et les parents.',path:'WIRE_SCHEMA · strictJson · validatePage'},
  {title:'Contrôles',Icon:IconShieldCheck,body:'Sommes des enfants directs, brut moins amortissements, puis égalité actif/passif. Les calculs utilisent des centimes entiers, sans flottants monétaires.',path:'BigInt · accounting · evaluate'},
  {title:'Comparaison',Icon:IconChartBar,body:'Chaque durée provient d’une nouvelle requête ou est explicitement marquée historique. Le JSON, les réponses brutes et les contrôles sont exportables.',path:'ResultsPanel · mesures de requêtes'},
];
export function ArchitectureView(){
  const [active,setActive]=useState(3);const item=steps[active];
  return <><div className="page-heading"><div><span className="eyebrow">Comprendre le fonctionnement</span><h1>Du bilan aux données contrôlées.</h1><p>Une chaîne lisible, avec des validations à chaque étape.</p></div></div>
    <section className="panel architecture"><div className="pipeline" aria-label="Étapes du traitement">{steps.map((step,i)=><div className="pipeline-node" key={step.title}><button aria-pressed={active===i} className={active===i?'active':''} onClick={()=>setActive(i)}><step.Icon size={26}/><strong>{step.title}</strong></button>{i<steps.length-1&&<IconArrowRight className="pipeline-arrow" size={19}/>}</div>)}</div>
      <div className="pipeline-detail"><item.Icon size={32}/><div><h2>{item.title}</h2><p>{item.body}</p><code>{item.path}</code></div></div></section>
    <div className="architecture-columns"><section className="panel"><IconCloud size={25}/><h2>Application web</h2><ul className="definition-list"><li><strong>Navigateur</strong><span>Lecture PDF.js, masques, choix des méthodes, affichage et exports.</span></li><li><strong>Serveur</strong><span>Vinext, validation des requêtes, appel HTTP au fournisseur et mesure de durée.</span></li><li><strong>Gemini</strong><span>Exécution distante avec la clé saisie pour la session.</span></li><li><strong>Ollama</strong><span>Exécution sur le PC, uniquement depuis la version locale.</span></li></ul></section>
      <section className="panel"><IconBook2 size={25}/><h2>Expérimentation notebook</h2><ul className="definition-list"><li><strong>PyMuPDF et Pillow</strong><span>Rendu 200 DPI et préparation des images du TP.</span></li><li><strong>Python Decimal</strong><span>Contrôles monétaires exacts et validation indépendante.</span></li><li><strong>Référence annotée</strong><span>88 postes et 107 montants sur le bilan fourni.</span></li><li><strong>Journaux conservés</strong><span>55 expériences archivées, échecs compris.</span></li></ul></section></div>
    <section className="panel contract"><div><span className="eyebrow">Un contrat explicite</span><h2>Un JSON valide peut contenir un montant faux.</h2><p>La structure, la cohérence comptable et la fidélité au document sont évaluées séparément. Une valeur illisible reste absente, avec son état ; elle n’est pas inventée pour équilibrer le bilan.</p><p className="muted">Sur un document nouveau, aucun pourcentage d’exactitude n’est annoncé sans référence annotée.</p></div><pre>{JSON.stringify({poste:'Clients et comptes rattachés',rubrique:'actif',montant_net_N:'18300692.45',montant_net_N1:'18556410.52'},null,2)}</pre></section>
  </>;
}

const questions=[
  ['Pourquoi un VLM ?','Il associe la lecture des chiffres à la structure visuelle du tableau, notamment les colonnes N/N−1, les amortissements et les sous-totaux.'],
  ['Quelles méthodes sont comparées ?','Consigne simple, rôle, contraintes, exemple fictif, mode JSON natif, schéma contraint, et Qwen local avec Ollama.'],
  ['Comment la vitesse est-elle mesurée ?','Le serveur mesure chaque requête avec une horloge monotone. La durée d’une méthode additionne ses requêtes de pages ; le temps de préparation du document est séparé.'],
  ['Peut-on annoncer une exactitude sur mon propre bilan ?','Seulement avec une référence vérifiée. Pour un document inconnu, l’application affiche la validité du JSON et les contrôles de cohérence, pas une précision inventée.'],
  ['Que signifie une cellule vide ?','Une case vide reste null. Un zéro imprimé est une valeur 0.00. Une valeur illisible est signalée et rend les contrôles correspondants indéterminés.'],
  ['Pourquoi Qwen local exige-t-il la version PC ?','Ollama tourne sur la machine locale. Un serveur hébergé ne peut pas accéder à votre boucle locale. Lancer la version locale permet au même serveur de joindre Ollama.'],
  ['Quelles limites ont été observées ?','Le petit VLM local a commis des erreurs de colonnes, de signes, de cellules et d’année. Le schéma a nécessité un motif regex portable. L’API a atteint le plafond sur le bilan de travail, sans test indépendant.'],
  ['Comment traiter la confidentialité ?','Vérifier les images préparées, masquer les données sensibles et autoriser leur envoi. Pour les données personnelles, examiner les conditions du fournisseur et les formalités CNDP applicables. Le local ne garantit pas à lui seul la conformité.'],
];
export function ProjectView(){
  return <><div className="page-heading"><div><span className="eyebrow">ENSAM Casablanca · Transformers et LLMs</span><h1>Le projet, de l’objectif au bilan.</h1><p>Extraire des tableaux de bilans marocains et vérifier ce que le modèle produit.</p></div><a className="button secondary compact" href="/data/compte-rendu.md" download><IconDownload size={17}/>Compte-rendu</a></div>
    <section className="project-intro"><div><span className="eyebrow">Objectif du TP</span><h2>Rendre un bilan exploitable par du code.</h2><p>Reconnaître les postes actif/passif dans un PDF ou une image, produire un JSON structuré, contrôler les totaux et mesurer les erreurs. L’application rend cette expérience reproductible sur vos documents.</p></div><div className="project-number"><strong>7</strong><span>méthodes réunies<br/>dans un même laboratoire</span></div></section>
    <div className="architecture-columns"><section className="panel"><IconFolder size={25}/><h2>Contenu du projet</h2><pre className="file-tree">{`VLM/\n├─ TP_Extraction_Bilans_VLM_Groupe9.ipynb\n├─ outputs_vlm/\n│  ├─ runs/             essais et réponses brutes\n│  ├─ compte_rendu.md   méthode et limites\n│  └─ comparaison_finale.csv\n└─ webapp/\n   ├─ app/             interface et API\n   ├─ lib/engine.ts    prompts et contrôles\n   └─ public/data/     exemple anonymisé`}</pre><p className="muted">Le notebook complet et les sources se trouvent dans le projet local. Le site utilise un exemple raster anonymisé.</p></section>
      <section className="panel"><IconCode size={25}/><h2>Ce qui est réellement vérifié</h2><ul className="definition-list"><li><strong>Exemple du TP</strong><span>Un bilan réel, deux pages, 88 postes, 107 montants de référence.</span></li><li><strong>API retenue</strong><span>107/107 montants exacts et 66 contrôles conformes dans l’essai principal archivé.</span></li><li><strong>Local</strong><span>Qwen3-VL 4B Instruct exécuté sur CPU ; résultats métier rejetés.</span></li><li><strong>Robustesse</strong><span>Scan dégradé synthétique et lot de deux fichiers issus du même bilan.</span></li></ul></section></div>
    <section className="panel questions"><div className="section-heading"><h2>Les questions du TP</h2><span className="muted">Méthode, validation et limites</span></div>{questions.map(([title,text])=><details key={title}><summary>{title}</summary><p>{text}</p></details>)}</section>
    <section className="source-links"><h2>Documentation de référence</h2><a href="https://ai.google.dev/gemini-api/docs/structured-output" target="_blank" rel="noreferrer">Gemini · sorties structurées <IconArrowRight size={16}/></a><a href="https://docs.ollama.com/capabilities/structured-outputs" target="_blank" rel="noreferrer">Ollama · schéma JSON <IconArrowRight size={16}/></a><a href="https://www.cndp.ma/transfert-de-donnees-a-letranger/" target="_blank" rel="noreferrer">CNDP · transfert à l’étranger <IconArrowRight size={16}/></a></section>
  </>;
}
