import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {strictJson,validatePage,cents,accounting,evaluate,runPage,ExtractInput} from '../lib/engine.ts';

test('JSON strict, montants exacts et contrôles comptables',()=>{
  assert.throws(()=>strictJson('```json\n{}\n```'));
  assert.throws(()=>strictJson('{"x":1,"\\u0078":2}'));
  assert.deepEqual(strictJson('{"a":{"x":1},"b":{"x":2}}'),{a:{x:1},b:{x:2}});
  assert.equal(cents('-9007199254740993.01'),-900719925474099301n);
  assert.throws(()=>cents('1,00'));
  const line={id:'A',poste:'Poste de test',parent_id:null,type_ligne:'total',valeurs:['120.00','20.00','100.00',null]};
  const wire={nature:'actif',exercice_N:2024,unite:'inconnue',preuve_unite:'',lignes:[line],avertissements:[]};
  const page=validatePage(wire);
  assert.equal(accounting([page])[0].statut,'ok');
  assert.throws(()=>validatePage({...wire,lignes:[{...line,valeurs:['NA','20.00','100.00',null]}]}));
  assert.throws(()=>validatePage({...wire,lignes:[line,line]}));
  assert.throws(()=>validatePage({...wire,lignes:[{...line,parent_id:'A'}]}));
  const wrong=validatePage({...wire,lignes:[{...line,valeurs:['120.00','20.00','99.00',null]}]});
  assert.equal(accounting([wrong])[0].statut,'ecart');
  const passif=validatePage({...wire,nature:'passif',lignes:[{...line,id:'P',valeurs:['NA','NA','100.00',null]}]});
  assert.equal(accounting([page,passif]).find(c=>c.controle==='Actif = passif').statut,'ok');
  const sample=JSON.parse(readFileSync(new URL('../public/data/extraction-exemple.json',import.meta.url),'utf8'));
  const reference=JSON.parse(readFileSync(new URL('../public/data/reference.json',import.meta.url),'utf8'));
  assert.equal(evaluate(sample.pages,reference).correct,107);
});

test('les six stratégies utilisent leur contrat natif et la clé ne sort pas',async()=>{
  const oldFetch=globalThis.fetch;
  const png=Buffer.alloc(33);png.set([137,80,78,71]);png.writeUInt32BE(1,16);png.writeUInt32BE(1,20);
  const raw=JSON.stringify({nature:'passif',exercice_N:2024,unite:'inconnue',preuve_unite:'',lignes:[{id:'P',poste:'Test',parent_id:null,type_ligne:'total',valeurs:['NA','NA','1.00',null]}],avertissements:[]});
  try{
    for(const method of ['baseline','role','constraints','fewshot','json_mode','schema']){
      globalThis.fetch=async(url,init)=>{
        assert.match(url,/^https:\/\/generativelanguage.googleapis.com\//);
        const body=JSON.parse(init.body);
        assert.equal(!!body.systemInstruction,method!=='baseline');
        assert.equal(!!body.generationConfig.responseMimeType,['json_mode','schema'].includes(method));
        assert.equal(!!body.generationConfig.responseJsonSchema,method==='schema');
        return Response.json({candidates:[{finishReason:'STOP',content:{parts:[{text:raw}]}}]});
      };
      const input=ExtractInput.parse({method,image:'data:image/png;base64,'+png.toString('base64'),page:1,apiKey:'private-test-key',consent:true});
      const result=await runPage(input,[],new AbortController().signal,false);
      assert.equal(result.ok,true);
      assert.ok(!JSON.stringify(result).includes('private-test-key'));
      const incomplete=await runPage({...input,knownExample:true},[{id:'P'},{id:'POSTE_ABSENT'}],new AbortController().signal,false);
      assert.equal(incomplete.ok,false);
      assert.match(incomplete.error,/Couverture incomplète/);
    }
  }finally{globalThis.fetch=oldFetch;}
});
