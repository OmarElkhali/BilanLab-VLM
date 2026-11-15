// Optional live integration check. Key arrives on hidden stdin, never in a file.
import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
process.stdin.setRawMode?.(true);process.stdin.resume();
console.log('Ready for API configuration on hidden stdin.');
const config=await new Promise(resolve=>{let text='';function read(chunk){text+=chunk.toString();if(/[\r\n]/.test(text)){process.stdin.off('data',read);process.stdin.pause();resolve(JSON.parse(text.trim()));}}process.stdin.on('data',read);});
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
  const page=await browser.newPage({viewport:{width:1440,height:1100}});
  const results=[];
  page.on('response',async response=>{if(response.url().endsWith('/api/extract'))results.push(await response.json());});
  await page.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});
  await page.getByRole('button',{name:'Exemple anonymisé',exact:true}).click();
  await page.getByRole('button',{name:'Agrandir la page'}).waitFor();
  for(const name of ['Consigne simple','Rôle système','Contraintes','Exemple fictif','Mode JSON','Qwen local'])await page.locator('.method-row').filter({has:page.getByText(name,{exact:true})}).getByRole('checkbox').uncheck();
  await page.locator('.top-actions').getByRole('button',{name:'Configuration'}).click();
  await page.getByLabel('Clé Gemini API',{exact:true}).fill(config.apiKey);
  await page.getByRole('button',{name:'Utiliser cette configuration'}).click();
  await page.locator('.consent').getByRole('checkbox').check();
  await page.getByRole('button',{name:/Lancer la comparaison/}).click();
  await page.getByRole('button',{name:/Annuler la comparaison/}).waitFor();
  await page.getByRole('button',{name:/Lancer la comparaison/}).waitFor({timeout:380000});
  await page.screenshot({path:'outputs/resultats-live.png',fullPage:true});
  assert.equal(results.length,2);
  assert.ok(results.every(r=>r.ok),results.map(r=>r.error).join('; '));
  await page.getByRole('tab',{name:'JSON'}).click();
  await page.getByRole('tab',{name:/Contrôles/}).click();
  const download=page.waitForEvent('download');
  await page.getByRole('button',{name:'Tout exporter'}).click();
  const file=await download;assert.equal(file.suggestedFilename(),'comparaison-bilan.json');
  assert.equal(await page.evaluate(()=>localStorage.length),0);
  console.log(JSON.stringify({live:true,method:'schema',pages:results.map(r=>({page:r.page,ok:r.ok,ms:r.durationMs,rows:r.data?.lignes.length})),exported:true}));
}finally{await browser.close();process.stdin.setRawMode?.(false);}
