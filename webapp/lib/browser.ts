export type Mask={x:number;y:number;w:number;h:number};
export type PreparedPage={src:string;width:number;height:number;masks:Mask[];name:string};
export async function prepareFiles(files:File[]):Promise<{pages:PreparedPage[];hash:string;name:string}>{
  if(!files.length)throw new Error('Choisir un PDF ou une image.');
  if(files.length>8)throw new Error('Huit images au maximum par bilan.');
  const pages:PreparedPage[]=[];const buffers:Uint8Array[]=[];
  for(const file of files){
    if(file.size>20_000_000)throw new Error('Chaque fichier doit faire moins de 20 Mo.');
    const bytes=new Uint8Array(await file.arrayBuffer());buffers.push(bytes);
    const pdf=file.type==='application/pdf'||file.name.toLowerCase().endsWith('.pdf');
    if(pdf){
      if(files.length!==1)throw new Error('Sélectionner un PDF unique ou plusieurs images.');
      const pdfjs=await import('pdfjs-dist');
      pdfjs.GlobalWorkerOptions.workerSrc='/pdfjs/pdf.worker.min.mjs';
      const task=pdfjs.getDocument({data:bytes.slice(),useSystemFonts:true});
      const document=await task.promise;
      try{
        if(document.numPages>8)throw new Error('Le bilan doit contenir au maximum huit pages.');
        for(let i=1;i<=document.numPages;i++){
          const page=await document.getPage(i);const first=page.getViewport({scale:1});
          const viewport=page.getViewport({scale:Math.min(2.5,1800/Math.max(first.width,first.height))});
          const canvas=window.document.createElement('canvas');canvas.width=Math.ceil(viewport.width);canvas.height=Math.ceil(viewport.height);
          const context=canvas.getContext('2d');if(!context)throw new Error('Rendu de page indisponible.');
          await page.render({canvasContext:context,canvas,viewport}).promise;
          pages.push({src:canvas.toDataURL('image/png'),width:canvas.width,height:canvas.height,masks:[],name:`Page ${i}`});
          page.cleanup();
        }
      }finally{await task.destroy();}
    }else{
      if(!['image/png','image/jpeg','image/webp'].includes(file.type))throw new Error('Formats acceptés : PDF, PNG, JPG et WebP.');
      const url=URL.createObjectURL(file);
      try{
        const image=new Image();image.src=url;await image.decode();
        if(image.naturalWidth*image.naturalHeight>40_000_000)throw new Error('Image trop grande. Réduire sa résolution.');
        const scale=Math.min(1,1800/Math.max(image.naturalWidth,image.naturalHeight));
        const canvas=window.document.createElement('canvas');canvas.width=Math.round(image.naturalWidth*scale);canvas.height=Math.round(image.naturalHeight*scale);
        canvas.getContext('2d')!.drawImage(image,0,0,canvas.width,canvas.height);
        pages.push({src:canvas.toDataURL('image/png'),width:canvas.width,height:canvas.height,masks:[],name:file.name});
      }finally{URL.revokeObjectURL(url);}
    }
  }
  const digest=files.length===1?await crypto.subtle.digest('SHA-256',buffers[0] as BufferSource):null;
  return {pages,hash:digest?Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join(''):'',name:files.map(f=>f.name).join(', ')};
}
export async function preparedImage(page:PreparedPage,local=false){
  const image=new Image();image.src=page.src;await image.decode();
  const scale=local?Math.min(1,1400/Math.max(page.width,page.height)):1;
  const canvas=document.createElement('canvas');canvas.width=Math.round(page.width*scale);canvas.height=Math.round(page.height*scale);
  const ctx=canvas.getContext('2d')!;ctx.fillStyle='#fff';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0,canvas.width,canvas.height);
  ctx.fillStyle='#fff';
  for(const mask of page.masks)ctx.fillRect(mask.x*canvas.width,mask.y*canvas.height,mask.w*canvas.width,mask.h*canvas.height);
  return canvas.toDataURL('image/png');
}
export function exportJson(value:unknown,name:string){
  const blob=new Blob([JSON.stringify(value,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);
  const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export const duration=(ms:number)=>ms>=60_000?`${Math.floor(ms/60_000)} min ${Math.round(ms%60_000/1000).toString().padStart(2,'0')} s`:`${(ms/1000).toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2})} s`;
export const money=(value:string|null)=>value===null?'—':value.replace(/\B(?=(\d{3})+(?!\d))/g,' ').replace('.',',');
