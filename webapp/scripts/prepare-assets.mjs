import {copyFile,mkdir} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const root=new URL('../',import.meta.url);
await mkdir(fileURLToPath(new URL('public/pdfjs/',root)),{recursive:true});
await copyFile(fileURLToPath(new URL('node_modules/pdfjs-dist/build/pdf.worker.min.mjs',root)),fileURLToPath(new URL('public/pdfjs/pdf.worker.min.mjs',root)));
console.log('PDF worker copied locally.');
