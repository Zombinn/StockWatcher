"""Web 前端 - 完整仪表盘（含配置管理）"""
from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)

router = APIRouter()

HTML_DASHBOARD = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>StockWatcher</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f1923;color:#e0e0e0}
.container{max-width:1400px;margin:0 auto;padding:16px;min-height:100vh;display:flex;flex-direction:column}
header{display:flex;justify-content:space-between;align-items:center;padding:16px 0;border-bottom:1px solid #1e3a5f;margin-bottom:20px}
header h1{color:#00d4aa;font-size:1.5em;cursor:pointer}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav a{color:#8899aa;text-decoration:none;padding:6px 14px;border-radius:6px;font-size:0.85em;cursor:pointer;transition:all .2s}
nav a:hover{background:#1a2d3d;color:#00d4aa}
nav a.active{background:#00d4aa22;color:#00d4aa}
.page{display:none;flex:1}
.page.active{display:block}
.card{background:#1a2d3d;border-radius:10px;padding:16px;margin-bottom:16px;border:1px solid #1e3a5f}
.card h2{color:#00d4aa;font-size:1.1em;margin-bottom:12px}
.stock-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
.stock-card{background:#1e3348;border-radius:8px;padding:14px;border:1px solid #2a4a6a}
.stock-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.stock-name{font-weight:600;font-size:1em}
.stock-code{color:#8899aa;font-size:0.8em}
.price{font-size:1.3em;font-weight:700}
.up{color:#ff4d4d}
.down{color:#00d4aa}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
@media(max-width:768px){.grid-2,.grid-3{grid-template-columns:1fr}}
.btn{background:#00d4aa;color:#0f1923;border:none;padding:8px 18px;border-radius:6px;font-size:0.9em;font-weight:600;cursor:pointer;transition:opacity .2s}
.btn:hover{opacity:.85}
.btn-sm{padding:4px 10px;font-size:0.8em}
.btn-danger{background:#ff4d4d;color:#fff}
.btn-outline{background:transparent;border:1px solid #00d4aa;color:#00d4aa}
input,select,textarea{padding:6px 10px;border-radius:6px;border:1px solid #2a4a6a;background:#0f1923;color:#e0e0e0;font-size:0.9em;margin:2px;outline:none;transition:border .2s;width:100%}
input:focus,select:focus,textarea:focus{border-color:#00d4aa}
textarea{resize:vertical;font-family:monospace}
label{display:block;color:#8899aa;font-size:0.85em;margin-bottom:4px;margin-top:10px}
label:first-child{margin-top:0}
.flex{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.ml-2{margin-left:8px}
.mt-2{margin-top:8px}
.mb-2{margin-bottom:8px}
.text-muted{color:#8899aa;font-size:0.85em}
.text-sm{font-size:0.85em}
.text-danger{color:#ff4d4d}
.text-success{color:#00d4aa}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:0.8em;font-weight:600}
.badge-green{background:#00d4aa22;color:#00d4aa;border:1px solid #00d4aa}
.badge-red{background:#ff4d4d22;color:#ff4d4d;border:1px solid #ff4d4d}
.badge-yellow{background:#ffc10722;color:#ffc107;border:1px solid #ffc107}
table{width:100%;border-collapse:collapse;font-size:0.9em}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid #1e3a5f}
th{color:#8899aa;font-weight:500;font-size:0.8em;text-transform:uppercase}
pre{background:#0f1923;border-radius:6px;padding:12px;overflow-x:auto;font-size:0.85em;line-height:1.5;white-space:pre-wrap}
.empty-state{text-align:center;padding:40px;color:#8899aa}

/* Config specific */
.config-section{margin-bottom:24px}
.config-section h3{color:#00d4aa;font-size:1em;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #1e3a5f}
.config-field{margin-bottom:8px}
.config-hint{color:#6a7a8a;font-size:0.8em;margin-top:2px}
.config-actions{padding:16px 0;display:flex;gap:12px}
.toast{position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;z-index:999;animation:slideIn .3s;max-width:400px}
.toast.success{background:#00d4aa22;color:#00d4aa;border:1px solid #00d4aa}
.toast.error{background:#ff4d4d22;color:#ff4d4d;border:1px solid #ff4d4d}
.toast.info{background:#2196f322;color:#64b5f6;border:1px solid #64b5f6}
@keyframes slideIn{from{opacity:0;transform:translateX(40px)}to{opacity:1;transform:translateX(0)}}
.spinner{display:inline-block;width:16px;height:16px;border:2px solid #00d4aa44;border-top-color:#00d4aa;border-radius:50%;animation:spin .6s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class=container>
<header>
<h1 onclick="switchPage('analysis')">📊 StockWatcher</h1>
<nav>
<a class=active onclick="switchPage('analysis',this)">分析</a>
<a onclick="switchPage('market',this)">大盘</a>
<a onclick="switchPage('portfolio',this)">持仓</a>
<a onclick="switchPage('alerts',this)">告警</a>
<a onclick="switchPage('agent',this)">问股</a>
<a onclick="switchPage('backtest',this)">回测</a>
<a onclick="switchPage('config',this)">⚙ 配置</a>
</nav>
</header>

<!-- 分析页 -->
<div id=page-analysis class="page active">
<div class="flex mb-2"><button class=btn onclick=runAnalysis()>🔄 执行分析</button><span id=analysisStatus class=text-muted>就绪</span></div>
<div id=analysisResults></div>
</div>

<!-- 大盘页 -->
<div id=page-market class=page>
<div class="flex mb-2"><button class=btn onclick=runMarketReview()>🔄 大盘复盘</button><span id=marketStatus class=text-muted>就绪</span></div>
<div class=grid-2 id=marketResults></div>
</div>

<!-- 持仓页 -->
<div id=page-portfolio class=page>
<div class="flex mb-2"><button class=btn onclick=loadPortfolio()>🔄 加载持仓</button><button class="btn btn-sm btn-outline" onclick=showAddPosition()>+ 添加</button><span id=portfolioStatus class=text-muted>就绪</span></div>
<div id=portfolioResults></div>
</div>

<!-- 告警页 -->
<div id=page-alerts class=page>
<div class="flex mb-2"><button class=btn onclick=loadAlerts()>🔄 加载告警</button><button class="btn btn-sm btn-outline" onclick=showAddAlert()>+ 添加规则</button><button class="btn btn-sm btn-outline" onclick=checkAlerts()>🔍 检查</button><span id=alertStatus class=text-muted>就绪</span></div>
<div id=alertResults></div>
</div>

<!-- 问股页 -->
<div id=page-agent class=page>
<div class="card"><div class="flex" style="flex-wrap:nowrap"><input id=agentCode placeholder="股票代码" style="width:120px"><input id=agentMsg placeholder="输入问题（如：技术面怎么样？）" style=flex:1><button class=btn onclick=startAgent() style=white-space:nowrap>💬 问股</button></div></div>
<div id=agentResults></div>
</div>

<!-- 回测页 -->
<div id=page-backtest class=page>
<div class="card"><div class="flex" style="flex-wrap:nowrap"><input id=btCode placeholder="股票代码" value=600519 style="width:120px"><select id=btStrategy style="width:130px"><option value=ma_cross>均线金叉</option><option value=macd>MACD</option><option value=rsi>RSI</option><option value=bollinger>布林带</option></select><button class=btn onclick=runBacktest() style=white-space:nowrap>🔄 回测</button><span id=btStatus class=text-muted></span></div></div>
<div id=btResults></div>
</div>

<!-- 配置页 -->
<div id=page-config class=page>
<div class="flex mb-2" style=justify-content:space-between>
<div><span id=configStatus class=text-muted></span></div>
<div class=flex><button class="btn btn-outline btn-sm" onclick=loadConfig()>🔄 刷新</button><button class="btn btn-sm" onclick=saveConfig()>💾 保存配置</button></div>
</div>
<div id=configResults></div>
<div id=configForm class=card style=display:none></div>
</div>

</div>

<script>
// --- Utils ---
async function api(url,opts={}){const r=await fetch(url,opts);const d=await r.json();if(!d.success)throw new Error(d.error||'请求失败');return d}
function toast(msg,type='success'){const t=document.createElement('div');t.className='toast '+type;t.textContent=msg;document.body.appendChild(t);setTimeout(()=>t.remove(),3000)}
function el(id){return document.getElementById(id)}
function show(id){el(id).style.display='block'}
function hide(id){el(id).style.display='none'}
async function apiPost(url,body){return api(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})}

function switchPage(id,el){
document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'))
document.querySelectorAll('nav a').forEach(a=>a.classList.remove('active'))
el(id).classList.add('active')
if(el)el.classList.add('active')
else document.querySelector(`nav a[onclick*="'${id}'"]`)?.classList.add('active')
}

// ===== 分析 =====
async function runAnalysis(){
el('analysisStatus').innerHTML='<span class=spinner></span> 分析中...'
el('analysisResults').innerHTML='<div class=card><p class=text-muted>⏳ 正在分析...</p></div>'
try{const d=await api('/api/v1/analyze');renderAnalysis(d)}catch(e){el('analysisResults').innerHTML='<div class=card><p class=text-danger>❌ '+e.message+'</p></div>'}
el('analysisStatus').textContent='✅ 完成'
}
function renderAnalysis(d){
let html='<div class=stock-grid>'
for(const[code,summary]of Object.entries(d.summaries||{})){html+='<div class=stock-card><pre style="white-space:pre-wrap;font-family:inherit;font-size:0.9em">'+summary+'</pre></div>'}
html+='</div>'
if(d.report)html+='<div class=card><h2>📄 完整报告</h2><pre>'+d.report+'</pre></div>'
el('analysisResults').innerHTML=html
}

// ===== 大盘 =====
async function runMarketReview(){
el('marketStatus').innerHTML='<span class=spinner></span> 复盘...'
el('marketResults').innerHTML='<div class=card><p class=text-muted>获取数据...</p></div>'
try{const d=await api('/api/v1/market/review');renderMarket(d)}catch(e){el('marketResults').innerHTML='<div class=card><p class=text-danger>❌ '+e.message+'</p></div>'}
el('marketStatus').textContent='✅ 完成'
}
function renderMarket(d){
let left='<div class=card><h2>📈 指数</h2>'
d.indices.forEach(i=>{left+=`<div class="flex" style=justify-content:space-between><span>${i.name}</span><span class=price style="font-size:1em;${i.change_pct>=0?'color:#ff4d4d':'color:#00d4aa'}">${i.price} (${i.change_pct>=0?'+':''}${i.change_pct}%)</span></div>`})
left+='</div><div class=card><h2>🔄 北向资金</h2>'
if(d.northbound){const n=d.northbound;left+=`<p>合计: <strong style="color:${n.total_net>=0?'#ff4d4d':'#00d4aa'}">${n.total_net>=0?'+':''}${n.total_net}亿</strong></p>`}
else left+='<p class=text-muted>暂无数据</p>'
left+='</div>'
let right='<div class=card><h2>🟢 领涨板块</h2>'
if(d.top_sectors&&d.top_sectors.length){d.top_sectors.forEach(s=>{right+=`<div class="flex" style=justify-content:space-between><span>${s.name}</span><span style=color:#ff4d4d>+${s.change_pct}%</span></div>`})}
right+='</div><div class=card><h2>🔴 领跌板块</h2>'
if(d.fall_sectors&&d.fall_sectors.length){d.fall_sectors.forEach(s=>{right+=`<div class="flex" style=justify-content:space-between><span>${s.name}</span><span style=color:#00d4aa>${s.change_pct}%</span></div>`})}
right+='</div>'
if(d.llm_analysis){right+=`<div class=card><h2>🤖 AI 分析</h2><pre>${JSON.stringify(d.llm_analysis,null,2)}</pre></div>`}
el('marketResults').innerHTML=left+right
}

// ===== 持仓 =====
async function loadPortfolio(){
el('portfolioStatus').innerHTML='<span class=spinner></span>'
try{const d=await api('/api/v1/portfolio');renderPortfolio(d.data)}catch(e){el('portfolioResults').innerHTML='<div class=card><p class=text-danger>❌ '+e.message+'</p></div>'}
el('portfolioStatus').textContent='✅ 完成'
}
function renderPortfolio(d){
let html=`<div class=card><div class=grid-3><div><p class=text-muted>总市值</p><p style="font-size:1.5em;font-weight:700">${d.total_market_value.toFixed(2)}</p></div><div><p class=text-muted>总收益</p><p style="font-size:1.5em;font-weight:700;color:${d.total_profit>=0?'#ff4d4d':'#00d4aa'}">${d.total_profit>=0?'+':''}${d.total_profit.toFixed(2)} (${d.total_profit_pct>=0?'+':''}${d.total_profit_pct.toFixed(2)}%)</p></div><div><p class=text-muted>风险评分</p><p style="font-size:1.5em;font-weight:700;color:${d.risk_score>60?'#ff4d4d':d.risk_score>30?'#ffc107':'#00d4aa'}">${d.risk_score}/100</p></div></div></div>`
if(d.suggestion)html+=`<div class=card><p>💡 ${d.suggestion}</p></div>`
html+='<div class=card><table><tr><th>代码</th><th>名称</th><th>持仓</th><th>成本</th><th>现价</th><th>市值</th><th>盈亏</th><th>占比</th></tr>'
d.positions.forEach(p=>{html+=`<tr><td>${p.code}</td><td>${p.name}</td><td>${p.quantity}</td><td>${p.cost_price.toFixed(2)}</td><td>${p.current_price.toFixed(2)}</td><td>${p.market_value.toFixed(2)}</td><td style="color:${p.profit_pct>=0?'#ff4d4d':'#00d4aa'}">${p.profit_pct>=0?'+':''}${p.profit_pct.toFixed(2)}%</td><td>${p.weight.toFixed(1)}%</td></tr>`})
html+='</table></div>'
el('portfolioResults').innerHTML=html
}
function showAddPosition(){const c=prompt('股票代码');const q=parseInt(prompt('数量'));const p=parseFloat(prompt('成本价'));if(c&&q&&p){api('/api/v1/portfolio/positions?code='+c+'&quantity='+q+'&cost_price='+p).then(()=>{loadPortfolio();toast('已添加 '+c)})}}

// ===== 告警 =====
async function loadAlerts(){
el('alertStatus').innerHTML='<span class=spinner></span>'
try{const d=await api('/api/v1/alerts');renderAlerts(d)}catch(e){el('alertResults').innerHTML='<div class=card><p class=text-danger>❌ '+e.message+'</p></div>'}
el('alertStatus').textContent='✅ 完成'
}
function renderAlerts(d){
let html=''
if(d.stats)html+=`<div class=card><div class="flex" style=justify-content:space-between><span>📋 规则: ${d.stats.total_rules}</span><span>启用: ${d.stats.enabled_rules}</span><span>事件: ${d.stats.total_events}</span></div></div>`
if(d.rules.length){html+=`<div class=card><h2>告警规则</h2><table><tr><th>代码</th><th>类型</th><th>阈值</th><th>状态</th><th>操作</th></tr>`;d.rules.forEach(r=>{html+=`<tr><td>${r.code}</td><td>${r.rule_type}</td><td>${r.threshold}</td><td>${r.enabled?'✅':'❌'}</td><td><button class="btn btn-sm btn-danger" onclick="removeAlert('${r.id}')">删除</button></td></tr>`});html+='</table></div>'}
if(d.events.length){html+=`<div class=card><h2>最近事件</h2><table><tr><th>时间</th><th>消息</th></tr>`;d.events.slice(0,5).forEach(e=>{html+=`<tr><td class=text-sm>${e.timestamp.slice(0,19)}</td><td>${e.message}</td></tr>`});html+='</table></div>'}
el('alertResults').innerHTML=html||'<div class=card><p class=text-muted>暂无告警规则，点"+ 添加规则"创建</p></div>'
}
function showAddAlert(){const c=prompt('股票代码');const t=prompt('类型(price_above/price_below/change_pct/volume)','price_above');const v=parseFloat(prompt('阈值'));if(c&&t&&v){api('/api/v1/alerts/rules?code='+c+'&rule_type='+t+'&threshold='+v+'&name='+c).then(()=>{loadAlerts();toast('已添加告警规则')})}}
function removeAlert(id){api('/api/v1/alerts/rules/'+id,{method:'DELETE'}).then(()=>{loadAlerts();toast('已删除规则')})}
async function checkAlerts(){try{const d=await apiPost('/api/v1/alerts/check',{});toast('检查完成，触发 '+d.triggered+' 条告警',d.triggered?'info':'success');loadAlerts()}catch(e){toast(e.message,'error')}}

// ===== Agent =====
async function startAgent(){
const code=el('agentCode').value;const msg=el('agentMsg').value||'分析一下技术面'
if(!code)return toast('请输入股票代码','error')
el('agentResults').innerHTML='<div class=card><p><span class=spinner></span> AI 分析中...</p></div>'
try{const s=await api('/api/v1/agent/session?code='+code+'&name='+code);const d=await api('/api/v1/agent/chat?session_id='+s.session_id+'&message='+encodeURIComponent(msg));el('agentResults').innerHTML='<div class=card><h2>🤖 AI 分析: '+code+'</h2><pre>'+d.response+'</pre></div>'}catch(e){el('agentResults').innerHTML='<div class=card><p class=text-danger>❌ '+e.message+'</p></div>'}
}

// ===== 回测 =====
async function runBacktest(){
const code=el('btCode').value;const strategy=el('btStrategy').value
el('btStatus').innerHTML='<span class=spinner></span> 回测中...'
el('btResults').innerHTML='<div class=card><p class=text-muted>计算中...</p></div>'
try{const d=await api('/api/v1/backtest?code='+code+'&strategy='+strategy);renderBacktest(d.data)}catch(e){el('btResults').innerHTML='<div class=card><p class=text-danger>❌ '+e.message+'</p></div>'}
el('btStatus').textContent='✅ 完成'
}
function renderBacktest(d){
const isWin=d.total_return>=0
let html=`<div class=card><div class=grid-3><div><p class=text-muted>初始资金</p><p style=font-size:1.3em;font-weight:700>${d.initial_capital.toFixed(2)}</p></div><div><p class=text-muted>最终价值</p><p style=font-size:1.3em;font-weight:700>${d.final_value.toFixed(2)}</p></div><div><p class=text-muted>总收益</p><p style="font-size:1.3em;font-weight:700;color:${isWin?'#ff4d4d':'#00d4aa'}">${d.total_return>=0?'+':''}${d.total_return_pct.toFixed(2)}%</p></div></div></div>
<div class=card><div class=grid-3><div><p class=text-muted>年化收益</p><p style=font-size:1.1em>${(d.annual_return*100).toFixed(2)}%</p></div><div><p class=text-muted>最大回撤</p><p style=font-size:1.1em>${d.max_drawdown.toFixed(2)}%</p></div><div><p class=text-muted>胜率</p><p style=font-size:1.1em>${d.win_rate.toFixed(1)}%</p></div></div><div class=grid-3 style=margin-top:8px><div><p class=text-muted>交易次数</p><p>${d.total_trades}</p></div><div><p class=text-muted>夏普比率</p><p>${d.sharpe_ratio.toFixed(2)}</p></div><div><p class=text-muted>周期</p><p class=text-sm>${d.start_date} ~ ${d.end_date}</p></div></div></div>`
if(d.trades&&d.trades.length){html+=`<div class=card><h2>最近交易</h2><div style=max-height:300px;overflow-y:auto><table><tr><th>日期</th><th>操作</th><th>价格</th><th>数量</th><th>金额</th><th>理由</th></tr>`;d.trades.slice(-15).reverse().forEach(t=>{html+=`<tr><td class=text-sm>${t.date}</td><td style="color:${t.action==='buy'?'#ff4d4d':'#00d4aa'}">${t.action}</td><td>${t.price.toFixed(2)}</td><td>${t.shares}</td><td>${t.amount.toFixed(2)}</td><td class=text-sm>${t.reason}</td></tr>`});html+='</table></div></div>'}
el('btResults').innerHTML=html
}

// ===== 配置管理 =====
async function loadConfig(){
el('configStatus').innerHTML='<span class=spinner></span> 加载配置...'
el('configForm').style.display='none'
try{
const secs=await api('/api/v1/config/sections');const vals=await api('/api/v1/config/values')
renderConfig(secs.sections,vals.values,vals.status)
el('configStatus').textContent='✅ 已加载'
}catch(e){el('configStatus').textContent='❌ '+e.message;el('configResults').innerHTML='<div class=card><p class=text-danger>加载失败: '+e.message+'</p></div>'}
}

// 存储当前编辑的值
let configValues={}

function renderConfig(sections,values,status){
configValues={...values}
let html=''
if(status){html+=`<div class=card><div class="flex" style=justify-content:space-between><span>📄 .env 文件: ${status.exists?'✅ 存在':'❌ 未创建'}</span><span>可配置项: ${status.configurable_fields} 项</span></div></div>`}

html+='<form id=configFormElement>'
sections.forEach(sec=>{
html+=`<div class=config-section><h3>${sec.label}</h3>`
sec.fields.forEach(f=>{
const val=values[f.key]||''
const key=f.key;const label=f.label;const desc=f.description||''
const type=f.type;const ph=f.placeholder||''
html+=`<div class=config-field><label for=cfg-${key}>${label}</label>`
if(type==='boolean'){
const checked=val==='true'||val==='1'
html+=`<div class=flex><input type=checkbox id=cfg-${key} ${checked?'checked':''} onchange="configValues['${key}']=this.checked?'true':'false'" style=width:auto><span class=text-muted>${desc}</span></div>`
}else if(type==='select'){
html+=`<select id=cfg-${key} onchange="configValues['${key}']=this.value">`
f.options.forEach(o=>{html+=`<option value="${o}" ${val===o?'selected':''}>${o}</option>`})
html+=`</select><div class=config-hint>${desc}</div>`
}else if(type==='multiline'){
html+=`<textarea id=cfg-${key} rows=3 onchange="configValues['${key}']=this.value">${val}</textarea><div class=config-hint>${desc}</div>`
}else{
const inputType=type==='password'?'password':'text'
html+=`<input type=${inputType} id=cfg-${key} value="${val.replace(/"/g,'&quot;')}" placeholder="${ph}" onchange="configValues['${key}']=this.value"><div class=config-hint>${desc}</div>`
}
html+=`</div>`
})
html+=`</div>`
})
html+=`</form>`
el('configResults').innerHTML=html
el('configForm').style.display='block'
}

async function saveConfig(){
const updates={}
for(const[key,val]of Object.entries(configValues)){
const el=document.getElementById('cfg-'+key)
if(el&&el.type==='checkbox')continue // already handled by onchange
updates[key]=String(val)
}

el('configStatus').innerHTML='<span class=spinner></span> 保存中...'
try{
const d=await apiPost('/api/v1/config/update',{updates})
toast(d.message,'success')
if(d.restart_required)toast('部分配置需重启服务生效','info')
el('configStatus').textContent='✅ 已保存'
loadConfig()
}catch(e){toast('保存失败: '+e.message,'error');el('configStatus').textContent='❌ 保存失败'}
}

// 自动加载
loadConfig()
</script>
</body></html>"""


@router.get("/web", response_class=HTMLResponse)
async def web_ui():
    return HTML_DASHBOARD
