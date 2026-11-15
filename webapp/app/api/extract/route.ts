import {ExtractInput,runPage} from '@/lib/engine';
import catalogue from '@/lib/data/catalogue.json';

export async function POST(request:Request){
  const url=new URL(request.url);const origin=request.headers.get('origin');
  if(origin&&origin!==url.origin)return Response.json({error:'Origine non autorisée.'},{status:403});
  if(!request.headers.get('content-type')?.includes('application/json'))return Response.json({error:'Format JSON requis.'},{status:415});
  const maximum=5_000_000;
  if(Number(request.headers.get('content-length')??0)>maximum)return Response.json({error:'Requête trop grande.'},{status:413});
  try{
    const reader=request.body?.getReader();if(!reader)throw new Error('Requête vide.');
    const chunks:Uint8Array[]=[];let size=0;
    while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>maximum){await reader.cancel();return Response.json({error:'Requête trop grande.'},{status:413});}chunks.push(value);}
    const bytes=new Uint8Array(size);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
    const input=ExtractInput.safeParse(JSON.parse(new TextDecoder().decode(bytes)));
    if(!input.success)return Response.json({error:'Paramètres incomplets ou invalides. Vérifier le fichier, les modèles et l’autorisation de traitement.'},{status:400});
    const local=import.meta.env.DEV&&['localhost','127.0.0.1','[::1]'].includes(url.hostname);
    if(input.data.method==='local'&&!local)return Response.json({error:'Ollama nécessite la version locale sur le PC.'},{status:409});
    const hint=input.data.knownExample?(input.data.page===1?'actif':'passif'):null;
    const guide=catalogue.filter(row=>!hint||row.rubrique===hint).map(({id,poste,parent_id,type_ligne})=>({id,poste,parent_id,type_ligne}));
    const result=await runPage(input.data,guide,request.signal,local);
    return Response.json(result,{headers:{'cache-control':'no-store'}});
  }catch(error){
    if(request.signal.aborted)return new Response(null,{status:499});
    return Response.json({error:error instanceof SyntaxError?'Corps JSON invalide.':'Traitement impossible. Réessayer avec un fichier plus léger.'},{status:400});
  }
}
