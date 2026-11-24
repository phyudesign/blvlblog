const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:700},deviceScaleFactor:1});
await p.goto('file://'+process.cwd()+'/line1125.html');await p.waitForTimeout(600);const h=await p.evaluate(()=>document.body.scrollHeight);await p.setViewportSize({width:1200,height:h});await p.screenshot({path:'/home/claude/blvlblog/wp-content/uploads/2026/11/blvl-tcg-daily-20261125-line.jpg',type:'jpeg',quality:86});
await b.close()})()
