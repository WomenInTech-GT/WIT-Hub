const resources = [
 ['A résumé that opens doors','Résumés','A clear, no-fluff guide to your first résumé. Turn coursework and campus work into strengths.',8,'Free template','Read the guide','Guide','Applying','♧',['Start with your name, email, and a link to your work.','Describe projects with an action, your contribution, and the outcome.','Keep formatting consistent and proofread before sharing.']],
 ['Networking, minus the awkward','Networking','Start real conversations, not elevator pitches. Find your people one message at a time.',6,'Conversation starters','Read the guide','Guide','Starting out','☏',['Choose someone whose work makes you curious.','Ask one specific question about their experience.','Thank them for their time and follow up with what you learned.']],
 ['No experience? Start here.','Career exploration','Small ways to build skills before your first role. There is more than one way in.',10,'Action plan','Explore your options','Guide','Starting out','◎',['Choose a small problem you care about.','Build a simple solution and document your process.','Ask a peer for feedback and make one improvement.']],
 ['Tell your story with STAR','Interviews','Make your examples memorable with a simple structure for behavioral interviews.',9,'Practice worksheet','Start practicing','Worksheet','Applying','◯',['Situation: describe the context briefly.','Task and action: explain your responsibility and what you did.','Result: share the outcome and what you learned.']],
 ['Your portfolio, beyond the pixels','Portfolios','Write a case study that shows how you think, not just what you made.',11,'Case study template','Build your case study','Worksheet','Applying','⊞',['Introduce the problem and who it affected.','Explain your decisions, constraints, and iterations.','Show the outcome and reflect on what you would improve.']],
 ['Find your lane in tech','Career exploration','Compare paths in design, engineering, data, and product. There is more than one way in.',15,'Role comparison','Explore career paths','Guide','Starting out','⚑',['Explore the daily tasks of a few roles.','Try a small activity from each role that interests you.','Reflect on which tasks you enjoyed and want to practice.']],
 ['The technical interview toolkit','Interviews','A supportive prep plan for explaining your thinking, solving problems, and asking questions.',14,'Prep checklist','Open the toolkit','Checklist','Applying','‹/›',['Review the role and practice relevant fundamentals.','Explain your approach aloud before writing a solution.','Test your work and discuss tradeoffs with the interviewer.']],
 ['Make your LinkedIn feel like you','Networking','Create a clear profile and send an introduction that sounds human, not copied and pasted.',7,'Profile checklist','Read the guide','Checklist','Applying','♧',['Write a headline describing your interests and skills.','Add projects with a brief explanation of your contribution.','Introduce yourself with a specific reason for connecting.']],
 ['From class project to résumé bullet','Résumés','Show your contribution and impact, even when your experience started in the classroom.',5,'Before-and-after examples','See the examples','Guide','Applying','✎',['Name the project and your contribution.','Use a concrete action: designed, built, researched, or tested.','Include an honest outcome; avoid inventing metrics.']],
 ['Your First Design Portfolio','Portfolios','Build a portfolio that tells the story behind your work.',12,'Free portfolio checklist','Read the guide','Checklist','Starting out','⊞',['Choose two or three projects that show your thinking.','For each project, describe the problem, process, and outcome.','Credit collaborators and explain your own role.','Make your contact details easy to find and test your links.']],
 ['Questions to ask your interviewer','Interviews','Learn about the team, expectations, and support before your next role.',6,'Question worksheet','Start preparing','Worksheet','Applying','◯',['Ask what success looks like in the first few months.','Ask how the team gives feedback and supports learning.','Ask about collaboration and the next steps in the process.']],
 ['A small plan for your next step','Career exploration','Turn a big career question into a manageable weekly action.',4,'Planning worksheet','Make your plan','Worksheet','Starting out','◎',['Write down one thing you want to explore.','Choose an action you can finish this week.','Set a time to reflect and decide your next step.']]
].map((r,index)=>({title:r[0],category:r[1],description:r[2],minutes:r[3],detail:r[4],action:r[5],format:r[6],stage:r[7],icon:r[8],steps:r[9],index}));
const grid=document.querySelector('#guide-grid');
const search=document.querySelector('#resource-search');
const format=document.querySelector('#format');
const stage=document.querySelector('#stage');
const sort=document.querySelector('#sort');
const load=document.querySelector('#load-more');
const dialog=document.querySelector('#guide-dialog');
let category='All', limit=9;
function render(){
 const query=search.value.trim().toLocaleLowerCase();
 let filtered=resources.filter(r=>(category==='All'||r.category===category)&&(format.value==='all'||r.format===format.value)&&(stage.value==='all'||r.stage===stage.value)&&`${r.title} ${r.description} ${r.category}`.toLocaleLowerCase().includes(query));
 if(sort.value==='shortest')filtered.sort((a,b)=>a.minutes-b.minutes);
 if(sort.value==='title')filtered.sort((a,b)=>a.title.localeCompare(b.title));
 grid.replaceChildren();
 filtered.slice(0,limit).forEach(r=>{
  const card=document.createElement('article');card.className='guide-card';
  card.innerHTML=`<div class="guide-top"><span class="guide-symbol" aria-hidden="true">${r.icon}</span><span class="guide-category">${r.category}</span></div><h3>${r.title}</h3><p>${r.description}</p><small>${r.minutes} min read · ${r.detail}</small><button type="button">${r.action}<span aria-hidden="true">↗</span></button>`;
  card.querySelector('button').addEventListener('click',()=>openGuide(r));grid.append(card);
 });
 load.hidden=filtered.length<=limit;
 document.querySelector('#empty-state').hidden=filtered.length!==0;
 document.querySelector('#result-count').textContent=`Showing ${Math.min(limit,filtered.length)} of ${filtered.length} resources`;
 document.querySelector('.library-count').textContent=`${resources.length} free resources · Curated by Women in Tech`;
}
function openGuide(r){
 document.querySelector('#guide-title').textContent=r.title;
 const content=document.querySelector('#guide-content');content.replaceChildren();
 const intro=document.createElement('p');intro.textContent=r.description;content.append(intro);
 const list=document.createElement('ol');r.steps.forEach(step=>{const li=document.createElement('li');li.textContent=step;list.append(li)});content.append(list);
 dialog.showModal();
}
function update(){limit=9;render()}
search.addEventListener('input',update);[format,stage,sort].forEach(el=>el.addEventListener('change',update));
document.querySelectorAll('[data-category]').forEach(button=>button.addEventListener('click',()=>{category=button.dataset.category;document.querySelectorAll('[data-category]').forEach(b=>{const selected=b===button;b.classList.toggle('selected',selected);b.setAttribute('aria-pressed',String(selected))});update()}));
load.addEventListener('click',()=>{limit+=9;render()});
document.querySelector('[data-guide]').addEventListener('click',()=>openGuide(resources[9]));
document.querySelectorAll('.close-dialog,.close-guide').forEach(button=>button.addEventListener('click',()=>dialog.close()));
render();
