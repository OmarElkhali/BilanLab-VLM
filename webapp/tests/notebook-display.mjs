import {chromium} from '@playwright/test';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
  const page=await browser.newPage({viewport:{width:1440,height:1050}});
  await page.goto(pathToFileURL(resolve('../TP_Extraction_Bilans_VLM_Groupe9.html')).href,{waitUntil:'domcontentloaded'});
  await page.screenshot({path:'outputs/notebook-introduction.png'});
  for(const [text,name] of [['Analyse 2 — Exactitude','notebook-exactitude'],['Analyse 5 — Les 88 postes','notebook-tableaux'],['Analyse 9 — Coût','notebook-cout']]){
    const heading=page.getByRole('heading').filter({hasText:text}).first();await heading.scrollIntoViewIfNeeded();
    await page.screenshot({path:`outputs/${name}.png`});
  }
  assert.ok(await page.locator('table').count()>=40);
  assert.ok(await page.locator('img').count()>=14);
  const archive=page.locator('summary').filter({hasText:'Archives historiques complètes'}).first();
  await archive.click();assert.ok(await archive.evaluate(el=>el.parentElement.open));
  console.log('HTML notebook: headings, 40+ tables, 14+ images and raw archives verified.');
}finally{await browser.close();}
