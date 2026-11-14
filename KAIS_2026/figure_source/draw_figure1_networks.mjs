import fs from 'node:fs';
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require=createRequire(import.meta.url);
const root=new URL('./',import.meta.url).pathname;
const sharp=require(require.resolve('sharp',{paths:process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?[process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES]:[root]}));
const base=root+'fig1_reference_base.png';
const image=fs.readFileSync(base).toString('base64');
const points=[[842,139],[878,84],[965,64],[1052,98],[1080,137],[1051,184],[982,231],[919,216],[862,201],[891,176],[919,130],[1000,111],[1021,147],[936,179],[982,189]];
const training=[[0,1],[1,2],[2,3],[3,4],[4,5],[5,14],[14,6],[6,7],[7,8],[8,0],
                [0,9],[8,9],[9,7],[9,13],[13,7],[13,14],[14,7],[10,2],[10,13],
                [10,14],[2,11],[11,3],[12,3],[12,4],[12,5]];
const uniform=[[0,10],[1,10],[9,10],[10,12],[11,12],[12,14],[5,6]];
// A schematic observed graph can also include held-out positive edges.
// They are not drawn in panel (b), and negatives exclude them as well.
const heldout=[[0,3],[8,12]];
const [u,w,v]=[10,2,11];
const key=(a,b)=>[a,b].sort((x,y)=>x-y).join(':');
const edgeSet=new Set(training.map(([a,b])=>key(a,b)));
assert.equal(edgeSet.size,training.length);
const observed=new Set([...training,...heldout].map(([a,b])=>key(a,b)));
assert.equal(observed.size,training.length+heldout.length);
assert(edgeSet.has(key(u,w))&&edgeSet.has(key(w,v))&&!edgeSet.has(key(u,v)));
assert(!observed.has(key(u,v)),'two-hop sample is an observed edge');
for(const [a,b] of uniform)assert(!observed.has(key(a,b)),`sample ${a},${b} is an observed edge`);
let seen=new Set([0]), changed=true;
while(changed){changed=false; for(const [a,b] of training){if(seen.has(a)&&!seen.has(b)){seen.add(b);changed=true;}if(seen.has(b)&&!seen.has(a)){seen.add(a);changed=true;}}}
assert.equal(seen.size,points.length,'training graph must be connected');
const attrs={stroke:'#8A9198','stroke-width':'2.0','stroke-linecap':'round'};
const line=(a,b,{dx=0,dy=0,color=attrs.stroke,width=2,dash=null}={})=>
  `<line x1="${points[a][0]+dx}" y1="${points[a][1]+dy}" x2="${points[b][0]+dx}" y2="${points[b][1]+dy}" stroke="${color}" stroke-width="${width}" stroke-linecap="round"${dash?` stroke-dasharray="${dash}"`:''}/>`;
const node=(i,{dx=0,dy=0,highlight=false}={})=>
  `<circle cx="${points[i][0]+dx}" cy="${points[i][1]+dy}" r="8.3" fill="url(#${highlight?'nodeGreen':'nodeGray'})" stroke="${highlight?'#007D55':'#646E78'}" stroke-width="0.75"/>`;
const top=training.map(([a,b])=>line(a,b)).join('')+
          uniform.map(([a,b])=>line(a,b,{color:'#E6542E',width:2.4,dash:'6 5'})).join('')+
          points.map((_,i)=>node(i)).join('');
const dx=-4,dy=246;
const bot=training.map(([a,b])=>line(a,b,{dx,dy})).join('')+
          line(u,w,{dx,dy,color:'#008C55',width:3})+
          line(w,v,{dx,dy,color:'#008C55',width:3})+
          line(u,v,{dx,dy,color:'#008C55',width:2.3,dash:'6 4'})+
          points.map((_,i)=>node(i,{dx,dy,highlight:[u,w,v].includes(i)})).join('')+
          `<g font-family="Georgia,serif" font-style="italic" font-weight="bold" font-size="17" fill="#111111"><text x="894" y="377">u</text><text x="974" y="308">w</text><text x="1008" y="375">v</text></g>`;
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1577" height="997" viewBox="0 0 1577 997">
<title>Stable misselection and adaptive validation: revised schematic</title>
<desc>Embedded raster retains the selected figure; both panel b network diagrams are redrawn as vectors from one shared training graph. Solid highlighted edges u-w and w-v exist, and dashed u-v is a non-edge.</desc>
<defs><radialGradient id="nodeGray" cx="32%" cy="28%" r="70%"><stop offset="0" stop-color="#FAFCFD"/><stop offset="0.5" stop-color="#C4CBD0"/><stop offset="1" stop-color="#89939B"/></radialGradient><radialGradient id="nodeGreen" cx="32%" cy="28%" r="70%"><stop offset="0" stop-color="#73DBB3"/><stop offset="0.55" stop-color="#00A268"/><stop offset="1" stop-color="#007A4E"/></radialGradient></defs>
<image width="1577" height="997" href="data:image/png;base64,${image}"/>
<rect x="818" y="52" width="283" height="190" fill="#FFFFFF"/>${top}
<rect x="818" y="293" width="283" height="183" fill="#FFFFFF"/>${bot}
</svg>`;
fs.writeFileSync(root+'fig1_master.svg',svg);
await sharp(Buffer.from(svg),{density:144}).resize({width:3154}).png().toFile(root+'fig1_master.png');
const metadata={figure:'Figure 1',base:'user-selected four-panel figure; local graph cleanup',
  panels_b_training_graph:'same 15 nodes and same edges in both samplers',points,training_edges:training,
  schematic_heldout_positive_edges:heldout,uniform_sample_nonedges:uniform,two_hop:{u,w,v,training_edges:[[u,w],[w,v]],sampled_nonedge:[u,v]},
  checks:{training_graph_connected:true,negative_samples_exclude_all_observed_edges:true,two_hop_path_is_valid:true},
  image:{svg_canvas_pixels:[1577,997],png_pixels:[3154,1994],raster_background_with_vector_networks:true}};
fs.writeFileSync(root+'fig1_network_manifest.json',JSON.stringify(metadata,null,2)+'\n');
console.log(JSON.stringify({nodes:points.length,edges:training.length,nonedges:uniform.length,path:[u,w,v],output:root+'fig1_master.png'},null,2));
