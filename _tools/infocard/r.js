const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:700},deviceScaleFactor:1});
for(const [f,o] of [['op','blvl-tcg-daily-20261107-op.jpg'],['pk','blvl-tcg-daily-20261107-price.jpg']]){await p.goto('file://'+process.cwd()+'/'+f+'.html');await p.waitForTimeout(400);const h=await p.evaluate(()=>document.body.scrollHeight);await p.setViewportSize({width:1200,height:h});await p.screenshot({path:o,type:'jpeg',quality:86});}
await b.close()})()
