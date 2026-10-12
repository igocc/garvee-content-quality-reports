"""Render the frozen audit exports as a static, public report site."""
import html
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
E = lambda value: html.escape(str(value), quote=True)
LABELS = {'pass': '符合', 'partial': '部分符合', 'unknown': '证据不足', 'fail': '不符合', 'not_applicable': '不适用'}
NAMES = {'G-INTENT': '读者目的', 'G-VALUE': '内容价值', 'G-FACTS': '事实与引用', 'G-WHO': '作者与责任人', 'G-HOW': '创作与核验过程', 'G-AI': 'AI 内容指导', 'G-SPAM': '垃圾内容政策', 'G-REVIEWS': '产品评测指导', 'G-EXPERIENCE': '页面体验'}
DIMS = {'C': '内容清晰度', 'O': '结构与组织', 'R': '参考与依据', 'E': '独有价值', 'Ept': '专业能力', 'Exp': '实际经验', 'A': '权威性', 'T': '可信度'}

def link(url, label):
    if not str(url).startswith(('https://', 'http://')):
        return E(label)
    return f'<a href="{E(url)}" target="_blank" rel="noopener noreferrer">{E(label)}</a>'

def quotes(d, key):
    return ''.join(f'<blockquote><p>{E(q["quote"])}</p><cite>{E(q["source_id"])} · 字符 {q["start"]}–{q["end"]}</cite></blockquote>' for q in d['located_evidence'].get(key, []))

def shell(title, body, nav=''):
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="description" content="GARVEE 文章内容质量审核：Google 内容指导、CORE-EEAT 证据与修改建议。"><title>{E(title)} · GARVEE 内容审核</title><link rel="stylesheet" href="style.css"></head>
<body><header><a class="brand" href="index.html">GARVEE <span>内容质量审核</span></a><span class="edition">2026.10 / 审核快照</span></header>{nav}<main>{body}</main><footer>基于已完成的审核报告生成 · Google 指导与 CORE-EEAT 分列 · 非 Google 官方评分<br>未重新调用模型，未执行 AI 检测或查重。报告只代表本次证据范围。</footer></body></html>'''

def render(d):
    a = d['aaron']
    observed = datetime.fromisoformat(d['observed_at']).astimezone(ZoneInfo('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M')
    body = f'''<div class="eyebrow">ARTICLE QUALITY REVIEW</div><h1>{E(d['display_title'])}</h1><p class="subtitle">{E(d['article']['title'])}</p><p class="meta">{link(d['article']['canonical_url'], '查看原文 ↗')} · 审核时间 {observed}（北京时间）</p>
<div class="metrics"><div><span>证据覆盖率</span><strong>{a['evidence_coverage']}<small>%</small></strong><p>CORE-EEAT 已有证据覆盖</p></div><div><span>审核结论</span><strong class="text-metric">需要补证据</strong><p>{E(a['status'])} / {E(a['verdict'])}</p></div><div><span>质量总分</span><strong class="text-metric">暂未评分</strong><p>{E(a['score_state'])}</p></div></div>
<aside class="notice"><b>证据覆盖率不是质量得分。</b>缺失或无法核验的证据保持“未知”，不等于文章已被判定低质。当前审核范围有限，尚需人工校准判断；不预测搜索排名。</aside>
<nav class="toc" aria-label="报告目录"><a href="#changes">修改建议</a><a href="#google">Google 指导</a><a href="#aaron">CORE-EEAT</a><a href="#sources">引用出处</a><a href="#bounds">范围与版本</a></nav>
<section id="changes"><div class="section-head"><h2>优先修改建议</h2><span>{len(d['recommendations'])} 项</span></div><div class="changes">'''
    for r in d['recommendations']:
        body += f'<article class="change"><span class="priority {E(r["priority"])}">{E(r["priority"])}</span><div><h3>{E(r["action"])}</h3><span class="code">{E(r["item_id"])}</span>{quotes(d,r["item_id"])}</div></article>'
    body += '</div></section><section id="google"><h2>Google 内容指导</h2><p class="section-note">逐项保留官方依据与原审核结论。“AI 内容指导”是政策证据审查，不是 AI 写作概率检测。</p><div class="findings">'
    for f in d['google_findings']:
        body += f'<article class="finding"><div class="finding-head"><h3>{E(NAMES.get(f["id"],f["id"]))} <small>{E(f["id"])}</small></h3><span class="badge {E(f["state"])}">{E(LABELS.get(f["state"],f["state"]))}</span></div><p>{E(f["reason"])}</p>{quotes(d,f["id"])}<p class="source">{link(f["source_url"],"Google 官方依据 ↗")}</p></article>'
    body += '</div></section><section id="aaron"><h2>CORE-EEAT 证据框架</h2><p class="section-note">Aaron 框架结果独立展示。以下各维度显示证据覆盖率，均不是质量得分。</p><div class="dimensions">'
    for key, value in a['dimension_coverage'].items():
        body += f'<div><span>{E(key)} · {E(DIMS.get(key,key))}</span><b>{value}%</b><progress value="{value}" max="100">{value}%</progress></div>'
    body += '</div><details><summary>查看全部 80 项框架观察与对应证据</summary><div class="findings">'
    for f in d['items']:
        body += f'<article class="finding"><div class="finding-head"><h3>{E(f["id"])}</h3><span class="badge {E(f["state"])}">{E(LABELS.get(f["state"],f["state"]))}</span></div><p>{E(f["reason"])}</p>{quotes(d,f["id"])}</article>'
    body += '</div></details></section><section id="sources"><h2>引用出处与抓取状态</h2><p class="section-note">body 指原文章正文；reference-* 指本次抓取的参考来源。未成功取回不代表该来源不存在或内容错误。</p><div class="table-wrap"><table><thead><tr><th>证据 ID</th><th>来源</th><th>状态</th></tr></thead><tbody>'
    for source in d['sources']:
        body += f'<tr><td>{E(source["id"])}</td><td>{link(source["url"],source["url"])}</td><td>{"已取回" if source["status"] == "retrieved" else "未取回"}</td></tr>'
    body += '</tbody></table></div></section><section id="bounds"><h2>范围与版本</h2><div class="boundary"><h3>AI 检测／查重：未执行</h3><p>原审核请求包含检测，但 Originality.ai 未配置，实际未执行。本文页不提供 AI 概率、原创率或相似率。</p><h3>审核边界</h3><ul><li>只审核两篇文章，不能代表 buying-guides 整个目录或全站。</li><li>主要依据 HTML 文本提取，未做页面视觉、移动端或性能验证。</li><li>模型判断经过证据定位和结构校验，不能替代全部事实的人工核验。</li><li>有限的引用集合不能证明完整原创性或全站权威性。</li></ul></div>'
    body += f'<details><summary>冻结版本与审计标识</summary><pre>{E(json.dumps({"audit_id":d["audit_id"],"observed_at":d["observed_at"],"versions":d["versions"]},ensure_ascii=False,indent=2))}</pre></details><p class="downloads">{link("https://github.com/igocc/garvee-content-quality-reports", "GitHub 仓库 ↗")} · <a href="reports/{E(d["slug"])}.md" download>下载原 Markdown</a> · <a href="reports/{E(d["slug"])}.json" download>下载公开报告数据</a></p></section>'
    return shell(d['display_title'], body, '<div class="back"><a href="index.html">← 返回报告列表</a></div>')

reports = [json.loads(p.read_text()) for p in sorted((ROOT/'reports').glob('*.json'))]
for d in reports:
    (ROOT/(d['slug']+'.html')).write_text(render(d))
cards = ''.join(f'<a class="report-card" href="{E(d["slug"])}.html"><div class="eyebrow">{E(d["category"])}</div><h2>{E(d["display_title"])}</h2><p>{E(d["article"]["title"])}</p><div class="card-bottom"><span>证据覆盖率 <b>{d["aaron"]["evidence_coverage"]}%</b></span><span>查看报告 →</span></div></a>' for d in reports)
(ROOT/'index.html').write_text(shell('文章审核报告',f'<div class="eyebrow">CONTENT QUALITY / GOOGLE / CORE-EEAT</div><h1>文章内容质量审核</h1><p class="subtitle">把结论、证据和修改建议放在一起，便于逐项复核与编辑。</p><aside class="notice"><b>当前共 2 篇完整文章报告。</b>未执行 AI 检测或查重。证据覆盖率不等于质量得分；两篇均需补充证据，暂未评分。</aside><div class="report-grid">{cards}</div><p class="section-note">报告为 2026 年 10 月 12 日审核快照，公开发布不会重新审核或自动改变结论。</p>'))
print('Generated index and',len(reports),'article pages')
