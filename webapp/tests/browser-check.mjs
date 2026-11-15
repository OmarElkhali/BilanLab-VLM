import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1080}});
const errors=[];page.on('pageerror',error=>errors.push(error.message));
await mkdir('outputs',{recursive:true});
try{
  await page.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});
  await page.getByRole('heading',{name:'Comparer les méthodes.'}).waitFor();
  await page.screenshot({path:'outputs/comparer-desktop.png',fullPage:true});
  await page.getByRole('button',{name:'Exemple anonymisé',exact:true}).click();
  await page.getByRole('button',{name:'Agrandir la page'}).waitFor({timeout:30000});
  await page.getByRole('button',{name:'Page suivante'}).click();
  await page.getByRole('button',{name:'Masquer l’entête'}).click();
  await page.getByRole('button',{name:'Agrandir la page'}).click();
  await page.getByRole('button',{name:'Fermer le zoom'}).click();
  await page.screenshot({path:'outputs/document-desktop.png',fullPage:true});
  for(const name of ['Résultats du TP','Architecture','Le projet']){
    await page.getByRole('navigation').getByRole('link',{name,exact:true}).click();
    await page.waitForTimeout(250);
    assert.ok((await page.locator('main').innerText()).length>300);
    await page.screenshot({path:'outputs/'+(name==='Architecture'?'architecture':name==='Le projet'?'projet':'historique')+'.png',fullPage:true});
  }
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('navigation').getByRole('link',{name:'Comparer',exact:true}).click();
  await page.screenshot({path:'outputs/comparer-mobile.png',fullPage:true});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'No horizontal page overflow');
  assert.deepEqual(errors,[]);
  console.log('Browser: PDF, navigation, masks, zoom and mobile passed.');
}finally{await browser.close();}
