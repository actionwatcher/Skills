#!/usr/bin/env node
// Parse the manufacturing files. Make separate board and layer images.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

// Join outline segments without discarding arcs with the same endpoints.
function outlineShape(plots) {
  const pending=[];
  for (const layer of plots.layers.filter(l=>l.type==='outline')) {
    for (const child of plots.plotTreesById[layer.id].children) {
      if (!['imagePath','imageRegion'].includes(child.type)) throw Error('The outline uses an unsupported primitive.');
      for (const segment of child.segments) {
        if (!['line','arc'].includes(segment.type)) throw Error('The outline uses an unsupported segment.');
        pending.push(segment);
      }
    }
  }
  const near=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1])<0.00001;
  const reverse=s=>({...s,start:s.end,end:s.start});
  const regions=[],points=[];
  while (pending.length) {
    const segments=[pending.shift()];
    while (!near(segments[0].start,segments[segments.length-1].end)) {
      const end=segments[segments.length-1].end;
      const matches=[];
      pending.forEach((s,i)=>{if(near(end,s.start)||near(end,s.end))matches.push(i);});
      if(matches.length!==1)throw Error('The outline is open or has a branch.');
      const next=pending.splice(matches[0],1)[0];
      segments.push(near(end,next.start)?next:reverse(next));
    }
    regions.push({type:'imageRegion',segments});
    for(const s of segments) {
      points.push(s.start,s.end);
      if(s.type==='arc') {
        const lo=Math.min(s.start[2],s.end[2]),hi=Math.max(s.start[2],s.end[2]);
        if(!Number.isFinite(lo)||!Number.isFinite(hi)||!Number.isFinite(s.radius))throw Error('The outline arc is not supported.');
        for(let n=Math.ceil(lo/(Math.PI/2));n<=Math.floor(hi/(Math.PI/2));n++) {
          const angle=n*Math.PI/2;
          points.push([s.center[0]+s.radius*Math.cos(angle),s.center[1]+s.radius*Math.sin(angle)]);
        }
      }
    }
  }
  if(!regions.length)throw Error('The board outline is missing.');
  const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
  return {regions,openPaths:[],size:[Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)]};
}

async function main() {
  const args = process.argv.slice(2);
  if (args.includes('--help')) {
    console.log('Use: node inspect_manufacturing.cjs --input DIRECTORY --out NEW_DIRECTORY');
    return;
  }
  const {read, plot, renderLayers, renderBoard, stringifySvg} = require('@tracespace/core');
  const options = {};
  for (let i=0; i<args.length; i+=2) {
    if (!['--input','--out'].includes(args[i]) || !args[i+1]) throw Error('Use --help for the arguments.');
    options[args[i].slice(2)] = path.resolve(args[i+1]);
  }
  if (!options.input || !options.out || !fs.statSync(options.input).isDirectory()) throw Error('Give a manufacturing directory.');
  if (fs.existsSync(options.out)) throw Error('Use a new output directory.');
  const files = fs.readdirSync(options.input).sort().map(name => {
    const full = path.join(options.input,name);
    if (!fs.lstatSync(full).isFile()) throw Error('The input must contain files only: '+name);
    return {name, full, sha256:crypto.createHash('sha256').update(fs.readFileSync(full)).digest('hex')};
  });
  const jobs = files.filter(f=>f.name.endsWith('.gbrjob'));
  for (const file of jobs) JSON.parse(fs.readFileSync(file.full,'utf8'));
  const layers = files.filter(f=>!f.name.endsWith('.gbrjob'));
  if (!layers.length) throw Error('No manufacturing layers were found.');
  fs.mkdirSync(options.out,{recursive:true});
  const errors=[];
  const result=await read(layers.map(f=>f.full));
  function examine(node, file) {
    if (/error|warning|unknown/i.test(node.type || '')) errors.push({file,type:node.type,message:node.message || node.value || ''});
    for (const child of node.children || []) examine(child,file);
  }
  for (const layer of result.layers) {
    examine(result.parseTreesById[layer.id],layer.filename);
    const entry=files.find(f=>f.name===layer.filename);
    if (!entry) throw Error('The parser returned an unknown file.');
    entry.type=layer.type; entry.side=layer.side;
    if (!layer.type) errors.push({file:layer.filename,message:'The layer type is unknown.'});
  }
  if (!result.layers.some(l=>l.type==='outline')) errors.push({message:'The board outline is missing.'});
  if (!result.layers.some(l=>l.type==='copper')) errors.push({message:'The copper layers are missing.'});
  const copperCount=result.layers.filter(l=>l.type==='copper').length;
  for (const layer of result.layers.filter(l=>l.type==='drill')) {
    const file=files.find(f=>f.name===layer.filename);
    const span=fs.readFileSync(file.full,'utf8').match(/TF\.FileFunction,(?:NonPlated|Plated),(\d+),(\d+),/);
    if (!span || Number(span[1])!==1 || Number(span[2])!==copperCount) {
      errors.push({file:file.name,message:'Use a viewer with drill span support for this drill file.'});
    }
  }
  const report={status:'blocked',files:files.map(({full,...f})=>f),errors,
                limits:['This check does not prove electrical connectivity.','Inspect the images before packaging.']};
  const reportPath=path.join(options.out,'inspection.json');
  if (!errors.length) {
    const plots=plot(result);
    try { plots.boardShape=outlineShape(plots); } catch(error) { errors.push({message:error.message}); }
    if (!errors.length) {
      const layerImages=renderLayers(plots), boardImages=renderBoard(layerImages);
      for (const side of ['top','bottom']) {
        const image=boardImages[side];
        const outer=image.children.find(n=>n.tagName==='g');
        const drilled=outer && outer.children.find(n=>n.tagName==='g' && n.properties.mask);
        if(!drilled)throw Error('The renderer has an unknown drill mask structure.');
        outer.properties.mask=drilled.properties.mask;
        fs.writeFileSync(path.join(options.out,side+'.svg'),stringifySvg(image));
      }
      for (const layer of layerImages.layers) fs.writeFileSync(path.join(options.out,layer.filename+'.svg'),stringifySvg(layerImages.rendersById[layer.id]));
      report.board_bounds_mm=plots.boardShape.size;
      report.status='passed';
    }
  }
  // Detect input changes during parsing and rendering.
  for (const f of files) {
    const hash=crypto.createHash('sha256').update(fs.readFileSync(f.full)).digest('hex');
    if (hash!==f.sha256) {report.status='blocked';errors.push({file:f.name,message:'The input changed.'});}
  }
  fs.writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({status:report.status,report:reportPath},null,2));
  if (report.status!=='passed') process.exitCode=3;
}
main().catch(error=>{console.error(error.message);process.exitCode=2;});
