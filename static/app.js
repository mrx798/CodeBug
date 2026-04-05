/* CodeBugEnv Frontend Logic — v2 Upgrade */
const API = localStorage.getItem('cbe_server_url') || '';
const S = {
  connected:false,tasks:[],activeTask:'syntax_fix',episodeRunning:false,episodeDone:false,
  currentStep:0,maxSteps:5,rewards:[],scoreHistory:[],buggyCode:'',observation:null,
  lastReq:null,lastRes:null,loading:false,estimatedSteps:2,logFilter:'All',
  hintText:'',showHint:false,previousScore:0,settings:{
    serverUrl:API,autoStart:false,showHints:true,animSpeed:'normal'
  }
};

function $(id){return document.getElementById(id)}
function timeNow(){return new Date().toLocaleTimeString('en-US',{hour12:false,hour:'2-digit',minute:'2-digit',second:'2-digit'})}
function rewardColor(v){return v>0.6?'var(--success)':v>0.3?'var(--warning)':'var(--error)'}

/* Load settings */
try{const s=JSON.parse(localStorage.getItem('cbe_settings')||'{}');Object.assign(S.settings,s)}catch(e){}

/* API */
async function apiFetch(path,opts={}){
  const url=(S.settings.serverUrl||API)+path;
  const isPost=opts.body!==undefined;
  const controller=new AbortController();const timeout=setTimeout(()=>controller.abort(),10000);
  S.lastReq={method:isPost?'POST':'GET',url,body:isPost?JSON.parse(opts.body):null};
  $('inspectorReq').textContent=JSON.stringify(S.lastReq,null,2);
  try{
    const r=await fetch(url,{method:isPost?'POST':'GET',headers:isPost?{'Content-Type':'application/json'}:{},body:isPost?opts.body:undefined,signal:controller.signal});
    clearTimeout(timeout);const data=await r.json();
    S.lastRes={status:r.status,data};$('inspectorRes').textContent=JSON.stringify(S.lastRes,null,2);
    if(!r.ok){throw new Error(`${r.status}: ${data.detail||JSON.stringify(data)}`)}
    return data;
  }catch(e){clearTimeout(timeout);if(e.name==='AbortError')throw new Error('Request timed out (10s)');throw e}
}

/* Toasts */
function showToast(msg,type='error'){
  const el=document.createElement('div');el.className=`toast toast-${type}`;el.textContent=msg;
  $('toasts').prepend(el);setTimeout(()=>{el.classList.add('dismissing');setTimeout(()=>el.remove(),200)},3000);
}

/* Log Feed */
function addLog(type,msg){
  const feed=$('logFeed');const entry=document.createElement('div');
  entry.className='log-entry';entry.dataset.type=type;
  entry.innerHTML=`<span class="log-time">${timeNow()}</span><span class="log-badge ${type}">${type}</span><span class="log-msg">${msg}</span>`;
  feed.prepend(entry);while(feed.children.length>50)feed.lastChild.remove();
  applyLogFilter();
}

function applyLogFilter(){
  document.querySelectorAll('.log-entry').forEach(e=>{
    if(S.logFilter==='All')e.classList.remove('hidden');
    else{const t=e.dataset.type;const map={Steps:'STEP',Rewards:'REWARD',Errors:'ERROR'};e.classList.toggle('hidden',t!==map[S.logFilter])}
  });
}

/* Task pills */
const TASK_META={syntax_fix:{label:'Syntax Fix',diff:'easy',key:'1'},logic_fix:{label:'Logic Fix',diff:'medium',key:'2'},security_fix:{label:'Security Fix',diff:'hard',key:'3'}};

function renderTaskPills(){
  const c=$('taskPills');c.innerHTML='';
  for(const[id,m]of Object.entries(TASK_META)){
    const p=document.createElement('div');p.className=`task-pill${S.activeTask===id?' active':''}`;
    p.innerHTML=`<span class="diff ${m.diff}">${m.diff}</span>${m.label}`;
    p.onclick=()=>switchTask(id);c.appendChild(p);
  }
}

function switchTask(tid){
  S.activeTask=tid;S.episodeRunning=false;S.episodeDone=false;S.currentStep=0;S.rewards=[];S.observation=null;S.buggyCode='';S.previousScore=0;S.showHint=false;
  renderTaskPills();updateTaskInfo();resetUI();addLog('INFO',`Switched to ${TASK_META[tid].label}`);
  if(S.settings.autoStart)startEpisode();
}

function updateTaskInfo(){
  const t=S.tasks.find(x=>x.task_id===S.activeTask);if(!t)return;
  $('taskInfoName').textContent=t.name;
  const b=$('taskInfoDifficulty');b.textContent=t.difficulty;b.className=`badge badge-${t.difficulty}`;
  $('taskInfoDesc').textContent=t.description;$('taskInfoTarget').textContent=t.target_score;$('taskInfoTests').textContent=t.num_test_cases;
  S.maxSteps=t.max_steps||5;
}

function resetUI(){
  $('codePlaceholder').style.display='flex';$('buggyCodePre').style.display='none';$('bugTypeBadge').style.display='none';
  $('fixedCodeInput').value='';$('bugExplanation').value='';$('confidenceBadge').style.display='none';
  $('rewardDisplay').style.display='none';$('submitError').textContent='';$('charCount').textContent='';
  $('statStep').innerHTML=`0<span style="font-size:13px;color:var(--text-muted)">/${S.maxSteps}</span>`;
  const s=$('statStatus');s.textContent='Idle';s.className='status-badge status-idle';
  $('statBest').textContent='—';$('statBest').style.color='var(--text-muted)';
  $('episodeOverlay').style.display='none';$('btnSubmit').disabled=true;$('btnStart').disabled=false;
  $('hintCallout').style.display='none';$('improvementBadge').textContent='';$('testsPills').innerHTML='';
  $('diffBarFill').style.width='0%';$('bugCategoryBadge').style.display='none';$('linesCount').textContent='';
  clearSparkline();drawSparkline();
}

/* Metrics bar */
async function refreshMetrics(){
  try{
    const m=await apiFetch('/metrics');
    $('mTotal').textContent=m.total_episodes;$('mSuccess').textContent=Math.round(m.success_rate*100)+'%';
    $('mBest').textContent=m.best_score_ever.toFixed(2);$('mSteps').textContent=m.avg_steps_to_solve.toFixed(1);
  }catch(e){}
}

/* Server health */
async function pingServer(){
  try{await apiFetch('/health');if(!S.connected){S.connected=true;$('statusDot').classList.add('connected');$('statusText').textContent=window.location.host;addLog('INFO','Connected to server')}}
  catch(e){S.connected=false;$('statusDot').classList.remove('connected');$('statusText').textContent='disconnected'}
}

async function loadTasks(){try{S.tasks=await apiFetch('/tasks');updateTaskInfo();addLog('INFO',`Loaded ${S.tasks.length} tasks`)}catch(e){addLog('ERROR',`Failed to load tasks: ${e.message}`)}}

/* Start Episode */
async function startEpisode(){
  if(S.loading)return;S.loading=true;$('btnStart').disabled=true;$('btnStart').innerHTML='<div class="spinner"></div>Starting...';$('episodeOverlay').style.display='none';
  try{
    const data=await apiFetch('/reset',{body:JSON.stringify({task_id:S.activeTask})});
    const obs=data.observation;S.observation=obs;S.buggyCode=obs.code;S.episodeRunning=true;S.episodeDone=false;S.currentStep=0;S.rewards=[];S.previousScore=0;S.showHint=false;
    S.estimatedSteps=obs.estimated_steps||2;
    $('codePlaceholder').style.display='none';const pre=$('buggyCodePre');pre.style.display='block';
    $('buggyCodeContent').textContent=obs.code;hljs.highlightElement($('buggyCodeContent'));pre.classList.add('code-fade-in');setTimeout(()=>pre.classList.remove('code-fade-in'),300);
    const taskType=S.activeTask.replace('_fix','');const bt=$('bugTypeBadge');bt.textContent=taskType;bt.className=`badge badge-${taskType}`;bt.style.display='inline-block';
    $('fixedCodeInput').value=obs.code;$('bugTypeSelect').value=taskType;updateCharCount();
    const lc=obs.code.split('\n').length;$('linesCount').textContent=`${lc} lines`;
    if(obs.bug_category){$('bugCategoryBadge').textContent=obs.bug_category.replace(/_/g,' ');$('bugCategoryBadge').style.display='inline-block'}
    const ds=obs.difficulty_score||0.5;$('diffBarFill').style.width=(ds*100)+'%';
    $('diffBarFill').style.background=ds>0.7?'var(--error)':ds>0.4?'var(--warning)':'var(--success)';
    $('statStep').innerHTML=`0<span style="font-size:13px;color:var(--text-muted)">/${S.maxSteps}</span>`;
    const s=$('statStatus');s.textContent='Running';s.className='status-badge status-running';
    $('statBest').textContent='0.00';$('statBest').style.color='var(--text-muted)';
    $('rewardDisplay').style.display='none';$('submitError').textContent='';$('btnSubmit').disabled=false;
    $('hintCallout').style.display='none';$('improvementBadge').textContent='';$('testsPills').innerHTML='';
    clearSparkline();drawSparkline();
    addLog('RESET',`Episode started for <b>${TASK_META[S.activeTask].label}</b>`);
    if(obs.error_message)addLog('INFO',`Error: ${obs.error_message}`);
    if(obs.hint&&S.settings.showHints)addLog('HINT',obs.hint);
  }catch(e){showToast(e.message);addLog('ERROR',e.message)}
  finally{S.loading=false;$('btnStart').innerHTML='<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>Start New Episode';$('btnStart').disabled=S.episodeRunning&&!S.episodeDone}
}

/* Submit Fix */
async function submitFix(){
  if(S.loading||!S.episodeRunning||S.episodeDone)return;
  S.loading=true;$('btnSubmit').disabled=true;$('btnSubmit').innerHTML='<div class="spinner"></div>Submitting...';$('submitError').textContent='';
  const action={fixed_code:$('fixedCodeInput').value,bug_explanation:$('bugExplanation').value||'No explanation',bug_type:$('bugTypeSelect').value,confidence:parseFloat($('confidenceSlider').value)/100};
  try{
    const data=await apiFetch('/step',{body:JSON.stringify({action})});
    const{observation:obs,reward,done,info}=data;S.observation=obs;S.currentStep=obs.current_step;
    const rT=reward.total,rG=reward.grader_score;S.rewards.push(rT);
    animateNumber($('rewardNumber'),rT);$('rewardDisplay').style.display='flex';$('rewardNumber').style.color=rewardColor(rT);
    $('rewardDetail').innerHTML=`Grader: ${rG.toFixed(3)} | Tests: ${(info.tests_passed||0)}/${(info.tests_total||0)} | Imp: ${(info.improvement||0)>0?'+':''}${(info.improvement||0).toFixed(3)}`;
    $('confidenceBadge').textContent=`Confidence: ${action.confidence.toFixed(2)}`;$('confidenceBadge').style.display='inline-block';
    $('statStep').innerHTML=`${obs.current_step}<span style="font-size:13px;color:var(--text-muted)">/${S.maxSteps}</span>`;
    const bs=obs.best_score||info?.best_score||0;$('statBest').textContent=bs.toFixed(2);$('statBest').style.color=rewardColor(bs);

    // Improvement badge
    const imp=info.improvement||0;
    const ib=$('improvementBadge');if(imp!==0){ib.textContent=(imp>0?'+':'')+imp.toFixed(3);ib.style.background=imp>0?'#22c55e18':'#ef444418';ib.style.color=imp>0?'var(--success)':'var(--error)'}else{ib.textContent=''}

    // Tests pills
    const tp=$('testsPills');tp.innerHTML='';if(info.tests_total){
      const c=info.tests_passed===info.tests_total?'var(--success)':info.tests_passed>0?'var(--warning)':'var(--error)';
      tp.innerHTML=`<span class="tests-pill" style="background:${c}18;color:${c}">${info.tests_passed}/${info.tests_total} tests</span>`}

    // Sparkline
    drawSparkline();

    // Hint
    if(info.hint&&info.hint.length>0&&S.settings.showHints){addLog('HINT',info.hint);S.hintText=info.hint}
    if(S.currentStep>=2&&rG<0.3){$('btnHint').style.display='inline-block'}else{$('btnHint').style.display='none'}

    if(obs.code){$('buggyCodeContent').textContent=obs.code;hljs.highlightElement($('buggyCodeContent'))}
    addLog('STEP',`Step ${obs.current_step} — Reward: <b>${rT.toFixed(3)}</b> | Grader: ${rG.toFixed(3)}`);
    if(info.tests_total)addLog('STEP',`Tests: ${info.tests_passed}/${info.tests_total} passed`);
    S.previousScore=rG;

    if(done){
      S.episodeDone=true;S.episodeRunning=false;
      const st=$('statStatus');st.textContent='Done';st.className='status-badge status-done';
      S.scoreHistory.unshift(bs);if(S.scoreHistory.length>5)S.scoreHistory.pop();renderScorePills();
      showEpisodeSummary(bs,obs.current_step);addLog('DONE',`Episode finished — Final: <b>${bs.toFixed(3)}</b>`);
      $('btnSubmit').disabled=true;$('btnStart').disabled=false;
      refreshMetrics();loadHistory();
    }else{$('btnSubmit').disabled=false}
  }catch(e){showToast(e.message);addLog('ERROR',e.message);if(e.message.includes('422'))$('submitError').textContent=e.message;$('btnSubmit').disabled=false}
  finally{S.loading=false;$('btnSubmit').innerHTML='Submit Fix <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>'}
}

/* Episode Summary Overlay */
function showEpisodeSummary(score,steps){
  const grade=score>0.9?'A':score>0.7?'B':score>0.5?'C':score>0.3?'D':'F';
  const gc=score>0.9?'var(--success)':score>0.7?'var(--accent)':score>0.5?'var(--warning)':score>0.3?'var(--warning)':'var(--error)';
  const speedMsg=steps<=1?'Lightning fast!':steps<=2?'Quick solve!':steps<=3?'Good pace':'Took a while';
  $('summaryScoreVal').textContent=score.toFixed(2);$('summaryScoreVal').style.color=gc;
  $('summaryGrade').textContent=grade;$('summaryGrade').style.background=gc+'18';$('summaryGrade').style.color=gc;
  $('summaryStepsVal').textContent=`${steps}/${S.maxSteps}`;$('summaryEstSteps').textContent=`(est: ${S.estimatedSteps})`;
  $('summarySpeed').textContent=speedMsg;$('summaryTask').textContent=TASK_META[S.activeTask]?.label||S.activeTask;
  $('episodeOverlay').style.display='flex';
}

function nextTask(){
  const tasks=['syntax_fix','logic_fix','security_fix'];const idx=tasks.indexOf(S.activeTask);
  switchTask(tasks[Math.min(idx+1,tasks.length-1)]);
}

/* Score pills */
function renderScorePills(){
  const c=$('scorePills');c.innerHTML='';if(!S.scoreHistory.length){c.innerHTML='<span style="font-size:11px;color:var(--text-muted)">No episodes</span>';return}
  S.scoreHistory.forEach(s=>{const p=document.createElement('span');p.className='score-pill';p.style.background=rewardColor(s).replace('var(','').replace(')','')+'18';p.style.color=rewardColor(s);p.textContent=s.toFixed(2);c.appendChild(p)});
}

/* Sparkline */
function clearSparkline(){S.rewards=[]}
function drawSparkline(){
  const canvas=$('sparklineCanvas');if(!canvas)return;const ctx=canvas.getContext('2d');
  canvas.width=canvas.offsetWidth*2;canvas.height=canvas.offsetHeight*2;ctx.scale(2,2);
  const w=canvas.offsetWidth,h=canvas.offsetHeight;ctx.clearRect(0,0,w,h);
  // Target line
  const task=S.tasks.find(t=>t.task_id===S.activeTask);
  if(task){const tgt=parseFloat(task.target_score?.replace(/[^0-9.]/g,''))||0.5;const ty=h-(tgt*h);
    ctx.setLineDash([4,4]);ctx.strokeStyle='#4a4a6a';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(0,ty);ctx.lineTo(w,ty);ctx.stroke();ctx.setLineDash([])}
  if(S.rewards.length<1)return;
  const pts=S.rewards;const step=w/Math.max(S.maxSteps-1,1);
  ctx.lineWidth=2;ctx.lineJoin='round';ctx.lineCap='round';
  ctx.beginPath();
  pts.forEach((v,i)=>{const x=i*step;const y=h-(v*h);if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y)});
  const lastColor=pts[pts.length-1]>0.6?'#22c55e':pts[pts.length-1]>0.3?'#f59e0b':'#ef4444';
  ctx.strokeStyle=lastColor;ctx.stroke();
  pts.forEach((v,i)=>{const x=i*step;const y=h-(v*h);ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fillStyle=lastColor;ctx.fill()});
}

/* Animate number */
function animateNumber(el,target){
  const start=parseFloat(el.textContent)||0;const diff=target-start;const dur=600;const t0=performance.now();
  function tick(now){const p=Math.min((now-t0)/dur,1);const e=1-Math.pow(1-p,3);el.textContent=(start+diff*e).toFixed(2);if(p<1)requestAnimationFrame(tick)}
  requestAnimationFrame(tick);
}

/* Char count */
function updateCharCount(){const v=$('fixedCodeInput').value;const lines=v.split('\n').length;const chars=v.length;$('charCount').textContent=`${lines} lines | ${chars} chars`}

/* Copy / Clear */
function copyBuggyCode(){if(!S.buggyCode)return;navigator.clipboard.writeText(S.buggyCode).then(()=>showToast('Copied!','success'))}
function clearFix(){$('fixedCodeInput').value='';updateCharCount()}

/* Hint */
function showHintCallout(){if(S.hintText){$('hintCallout').style.display='flex';$('hintText').textContent=S.hintText}else if(S.observation?.hint){$('hintCallout').style.display='flex';$('hintText').textContent=S.observation.hint}}
function dismissHint(){$('hintCallout').style.display='none'}

/* Inspector */
function toggleInspector(){$('inspectorToggle').classList.toggle('open');$('inspectorBody').classList.toggle('open')}

/* History */
async function loadHistory(){try{const h=await apiFetch('/history');renderHistory(h.slice(0,5))}catch(e){}}
function renderHistory(items){
  const c=$('historyList');c.innerHTML='';if(!items.length){c.innerHTML='<span style="font-size:11px;color:var(--text-muted)">No history</span>';return}
  items.forEach(ep=>{const d=document.createElement('div');d.className='history-card';
    const sc=rewardColor(ep.final_score);
    d.innerHTML=`<span class="badge badge-${TASK_META[ep.task_id]?.diff||'easy'}">${(TASK_META[ep.task_id]?.diff||'?').slice(0,1).toUpperCase()}</span><span style="font-weight:600;color:${sc}">${ep.final_score.toFixed(2)}</span><span style="color:var(--text-muted)">${ep.steps_taken} steps</span>`;
    c.appendChild(d)});
}

/* Log filters */
function setLogFilter(f){S.logFilter=f;document.querySelectorAll('.log-filter').forEach(b=>b.classList.toggle('active',b.dataset.filter===f));applyLogFilter()}
function clearFeed(){$('logFeed').innerHTML=''}

/* Theme toggle */
function toggleTheme(){
  const isLight=document.body.classList.toggle('light');localStorage.setItem('cbe_theme',isLight?'light':'dark');
  $('themeIcon').innerHTML=isLight?'<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>':'<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>';
}

/* Settings */
function openSettings(){$('settingsOverlay').classList.add('open');$('settingsPanel').classList.add('open')}
function closeSettings(){$('settingsOverlay').classList.remove('open');$('settingsPanel').classList.remove('open')}
function saveSettings(){
  S.settings.serverUrl=$('settingUrl').value||API;S.settings.autoStart=$('settingAutoStart').classList.contains('on');
  S.settings.showHints=$('settingShowHints').classList.contains('on');
  localStorage.setItem('cbe_settings',JSON.stringify(S.settings));localStorage.setItem('cbe_server_url',S.settings.serverUrl);
  showToast('Settings saved','success');closeSettings();
}
function toggleSetting(id){$(id).classList.toggle('on')}

/* Confidence slider */
$('confidenceSlider').oninput=function(){$('confidenceVal').textContent=(this.value/100).toFixed(2)};
$('fixedCodeInput').oninput=updateCharCount;
$('fixedCodeInput').addEventListener('keydown',e=>{if(e.key==='Tab'){e.preventDefault();const ta=e.target;const s=ta.selectionStart;ta.value=ta.value.substring(0,s)+'    '+ta.value.substring(ta.selectionEnd);ta.selectionStart=ta.selectionEnd=s+4}});

/* Keyboard shortcuts */
document.addEventListener('keydown',e=>{
  if(e.ctrlKey&&e.key==='Enter'){e.preventDefault();submitFix()}
  if(e.ctrlKey&&e.key==='r'){e.preventDefault();startEpisode()}
  if(e.ctrlKey&&e.key==='1'){e.preventDefault();switchTask('syntax_fix')}
  if(e.ctrlKey&&e.key==='2'){e.preventDefault();switchTask('logic_fix')}
  if(e.ctrlKey&&e.key==='3'){e.preventDefault();switchTask('security_fix')}
  if(e.ctrlKey&&e.key==='h'){e.preventDefault();showHintCallout()}
});

/* Wire buttons */
$('btnStart').onclick=startEpisode;$('btnSubmit').onclick=submitFix;
$('btnBaseline').onclick=async()=>{
  if(S.loading)return;addLog('INFO','Baseline simulation...');$('btnBaseline').disabled=true;
  try{await startEpisode();if(!S.episodeRunning)return;
    for(let i=0;i<S.maxSteps&&!S.episodeDone;i++){await new Promise(r=>setTimeout(r,600));$('bugExplanation').value=`Baseline attempt ${i+1}`;await submitFix()}
    addLog('INFO','Baseline complete');
  }catch(e){addLog('ERROR',e.message)}finally{$('btnBaseline').disabled=false}
};

/* Init */
async function init(){
  if(localStorage.getItem('cbe_theme')==='light')document.body.classList.add('light');
  renderTaskPills();addLog('INFO','CodeBugEnv v2 initialized');
  $('settingUrl').value=S.settings.serverUrl;
  if(S.settings.autoStart)$('settingAutoStart').classList.add('on');
  if(S.settings.showHints)$('settingShowHints').classList.add('on');
  await pingServer();if(S.connected){await loadTasks();refreshMetrics();loadHistory()}
  else addLog('ERROR','Server disconnected');
  setInterval(pingServer,5000);setInterval(refreshMetrics,10000);
}
init();
