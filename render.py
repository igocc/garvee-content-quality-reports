"""Render public frozen SEO/GEO data without running audit services."""
import html
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

PACKAGE_DATA = Path(__file__).resolve().parent
LABELS = {"pass": "符合", "partial": "部分符合", "fail": "不符合", "unknown": "证据不足", "not_applicable": "不适用"}


def render_html(report):
    e = lambda value: html.escape(str(value), quote=True)

    def anchor(url, label):
        try:
            scheme = urlsplit(str(url)).scheme
        except ValueError:
            scheme = ""
        return f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">{e(label)}</a>' if scheme in ("https", "http") else e(label)

    def raw(value):
        return '<pre>' + e(json.dumps(value, ensure_ascii=False, indent=2)) + '</pre>'

    def evidence(key):
        return ''.join(f'<blockquote><p>{e(ref["quote"])}</p><cite>{e(ref["source_id"])} · 字符 {ref["start"]}–{ref["end"]}</cite></blockquote>' for ref in report.get("located_evidence", {}).get(key, []))

    score = report["framework_result"]
    analysis = report.get("analysis")
    incomplete = not analysis or analysis.get("status") != "completed"
    title = report['article']['title']
    try:
        observed = datetime.fromisoformat(report["observed_at"]).astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M（北京时间）")
    except ValueError:
        observed = report["observed_at"]
    css = (PACKAGE_DATA / "style.css").read_text()
    body = f'<div class="eyebrow">SEO / GEO / EVIDENCE REVIEW</div><h1>{e(title)}</h1><p class="meta">{anchor(report["article"].get("canonical_url") or report["article"].get("url", ""), "查看原文 ↗")} · 审核时间 {e(observed)}</p>'
    body += f'<div class="metrics"><div><span>审核完成情况</span><strong class="text-metric">{"审核不完整" if incomplete else "分项执行完成"}</strong><p>每项服务状态单独记录</p></div><div><span>内容证据覆盖率</span><strong>{e(score.get("evidence_coverage", "—"))}<small>%</small></strong><p>不是质量得分</p></div><div><span>内容质量结论</span><strong class="text-metric">{"暂未评分" if score.get("score_state") == "NOT_SCORED" else "参考框架结果"}</strong><p>{e(score.get("status"))} / {e(score.get("score_state"))}</p></div></div>'
    body += '<aside class="notice"><b>SEO 与 GEO 分开报告。</b>页面代码观察、内容证据、服务启发式评分和本机向量检索模拟分别呈现；不作为 Google 官方分数或真实 AI 引用率。缺失观测保持待核验。</aside><nav class="toc"><a href="#seo">SEO 技术</a><a href="#geo">GEO 分析</a><a href="#changes">修改建议</a><a href="#content">Google 内容指导</a><a href="#framework">可信度证据框架</a><a href="#sources">引用出处</a></nav>'
    if analysis:
        seo = analysis['seo']
        body += '<section id="seo"><h2>SEO 技术与外链</h2><p class="section-note">源 HTML 的可复核观察。没有执行的渲染、索引和性能检查单独说明。</p><div class="findings">'
        for f in seo['technical'].get('findings', []):
            body += f'<article class="finding"><div class="finding-head"><h3>{e(f["label"])} <small>{e(f["id"])}</small></h3><span class="badge {e(f["state"])}">{e(LABELS.get(f["state"],f["state"]))}</span></div><p>{e(f["reason"])}</p><p class="source">{anchor(f["source_url"],"规则／技术参考 ↗")}</p><details><summary>查看源 HTML 观察</summary>{raw(f["evidence"])}</details></article>'
        if not seo['technical'].get('findings'):
            body += '<article class="finding">' + raw(seo['technical']) + '</article>'
        body += f'</div><div class="boundary"><h3>DataForSEO 外链：{e(seo["backlinks"]["status"])}</h3><p>{e(seo["backlinks"].get("reason", "来源是外链索引样本，不能单凭链接数量证明权威性。"))}</p><details><summary>外链接口结果与范围</summary>{raw(seo["backlinks"])}</details><h3>渲染 DOM：{e(analysis["rendered_dom"]["status"])}</h3><p>{e(analysis["rendered_dom"]["reason"])}</p></div></section><section id="geo"><h2>GEO 准备度与语义检索</h2><p class="section-note">两项真实服务的独立结果；输入为同一冻结材料。</p>'
        for name, label in (('optimizer', 'GEO Optimizer'), ('sage', 'SAGE / mcp-geo-server')):
            r = analysis['geo'][name]
            body += f'<article class="finding"><div class="finding-head"><h3>{label}</h3><span class="badge {"pass" if r["status"] == "completed" else "unknown"}">{"调用完成" if r["status"] == "completed" else "不可用"}</span></div>'
            if r['status'] != 'completed':
                body += f'<p>{e(r.get("reason"))}</p>'
            elif name == 'sage':
                m = r['raw'].get('metrics', {})
                g = m.get('geo', {})
                body += f'<p>实际后端：{e(g.get("embedding_backend"))}</p><p>CSP 检索代理值：<b>{e(g.get("citation_survival_proxy", "—"))}</b> / 100 · 段落块数：{e(g.get("chunk_count"))}</p><p>CSP 未校准为真实概率；不会把服务历史字段 probability 当作实际引用概率。</p>'
                suggestions = [f for f in r["raw"].get("findings", []) if f.get("recommendation") and f.get("status") not in ("pass", "info")]
                body += '<p>以下是服务自身的诊断建议，需结合证据判断，不等于 Google 要求：</p><ul>' + ''.join(f'<li><b>{e(f.get("title"))}</b>：{e(f["recommendation"])} <small>证据类别 {e(f.get("evidence", {}).get("level", "未提供"))}</small></li>' for f in suggestions) + '</ul>'
                body += '<details><summary>实体与结构观察</summary>' + raw(m.get('aeo', {})) + '</details>'
                body += '<details><summary>检索指标与假设</summary>' + raw(g) + '</details>'
            else:
                checks = r['raw'].get('checks', {})
                body += '<p>已运行 Schema、元数据、内容结构、实体、可引用性和事实信号检查。缺少来源／数字冲突等信号不能证明事实真伪。</p>'
                for key, label2 in [('brand_entity','实体与身份信号'),('citability','可引用性启发式结果'),('factual_signals','事实与来源信号')]:
                    body += f'<details><summary>{label2}</summary>{raw(checks.get(key, {}))}</details>'
            body += '<details><summary>版本、范围与原始服务结果</summary>' + raw(r) + '</details></article>'
        body += '<div class="notice">真实 AI 平台引用：未测量。本次包含本机准备度和检索模拟，不覆盖 ChatGPT／Gemini／Perplexity 真实答案。</div></section>'
    body += '<section id="changes"><h2>内容修改建议</h2><div class="changes">'
    for r in report.get('recommendations', []):
        body += f'<article class="change"><span class="priority {e(r["priority"])}">{e(r["priority"])}</span><div><h3>{e(r["action"])}</h3><span class="code">{e(r["item_id"])}</span>{evidence(r["item_id"])}</div></article>'
    body += '</div></section><section id="content"><h2>Google 内容指导与可信度证据</h2><div class="findings">'
    for f in report['google_findings']:
        body += f'<article class="finding"><div class="finding-head"><h3>{e(f["id"])}</h3><span class="badge {e(f["state"])}">{e(LABELS.get(f["state"],f["state"]))}</span></div><p>{e(f["reason"])}</p>{evidence(f["id"])}<p class="source">{anchor(f["source_url"],"Google 官方依据 ↗")}</p></article>'
    body += '</div></section><section id="framework"><h2>内容质量与可信度框架</h2><p class="section-note">框架结果独立展示。各维度显示证据覆盖率，不能当作质量得分；评分缺失时保留未评分状态。</p>'
    body += f'<p>框架状态：{e(score.get("status"))} / {e(score.get("verdict"))} / {e(score.get("score_state"))}</p><div class="dimensions">'
    dimensions = {"C": "内容清晰度", "O": "结构与组织", "R": "参考与依据", "E": "独有价值", "Ept": "专业能力", "Exp": "实际经验", "A": "权威性", "T": "可信度"}
    for key, coverage in score.get("dimension_coverage", {}).items():
        body += f'<div><span>{e(dimensions.get(key, key))} · 证据覆盖率</span><b>{e(coverage)}%</b></div>'
    body += '</div><details><summary>完整框架结果</summary>' + raw(score) + '</details><details><summary>全部内容观察与对应证据</summary><div class="findings">'
    for f in report['items']:
        body += f'<article class="finding"><h3>{e(f["id"])} · {e(LABELS.get(f["state"],f["state"]))}</h3><p>{e(f["reason"])}</p>{evidence(f["id"])}</article>'
    body += '</div></details></section><section id="sources"><h2>来源与审核边界</h2><div class="table-wrap"><table><thead><tr><th>证据</th><th>URL</th><th>状态</th></tr></thead><tbody>'
    for ref in report.get('source_references', []):
        body += f'<tr><td>{e(ref["id"])}</td><td>{anchor(ref["url"],ref["url"])}</td><td>{e(ref["status"])}</td></tr>'
    body += '</tbody></table></div><ul>' + ''.join(f'<li>{e(v)}</li>' for v in report.get('limitations', [])) + '</ul>'
    body += '<details><summary>冻结版本与模型</summary>' + raw({'audit_id':report['audit_id'],'versions':report['versions'],'model':report.get('model')}) + '</details>'
    body += '<details><summary>可选 AI 检测／查重状态</summary>' + raw(report.get('detection')) + '</details>'
    ident = e(report['audit_id'])
    body += f'<p class="downloads"><a href="{ident}.json" download>下载报告 JSON</a> · <a href="{ident}.md" download>下载 Markdown</a></p></section>'
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>{e(title)} · SEO / GEO 报告</title><style>{css}</style></head><body><header><span class="brand">GARVEE <span>SEO / GEO 分析报告</span></span><span class="edition">冻结审核快照</span></header><main>{body}</main><footer>证据优先 · 分项状态可追踪 · 非 Google 官方评分</footer></body></html>'
