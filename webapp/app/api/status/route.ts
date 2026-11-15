export async function GET(request:Request){
  const url=new URL(request.url);
  const local=import.meta.env.DEV&&['localhost','127.0.0.1','[::1]'].includes(url.hostname);
  let models:string[]=[];let available=false;
  if(local){try{
    const response=await fetch('http://127.0.0.1:11434/api/tags',{signal:AbortSignal.timeout(1500)});
    const data=await response.json() as {models?:{name:string}[]};
    models=(data.models??[]).map(m=>m.name).filter(name=>!/cloud/i.test(name));
    available=response.ok&&models.some(name=>/vl|vision|gemma/i.test(name));
  }catch{}}
  return Response.json({local,ollamaAvailable:available,localModels:models,apiModel:'gemini-3.1-flash-lite'},
    {headers:{'cache-control':'no-store'}});
}
