"""Rebuild pages from public frozen report data; no audit or API calls."""
import html
import json
from pathlib import Path

from render import render_html

ROOT = Path(__file__).resolve().parent
E = lambda value: html.escape(str(value), quote=True)
reports = [json.loads(p.read_text()) for p in sorted((ROOT / "reports").glob("*.json"))]
for report in reports:
    page = render_html(report)
    ident, slug = report["audit_id"], report["slug"]
    for suffix in ("json", "md"):
        page = page.replace(f'href="{ident}.{suffix}"', f'href="reports/{slug}.{suffix}"')
    page = page.replace('<main>', '<div class="back"><a href="index.html">← 返回报告列表</a></div><main>', 1)
    (ROOT / (slug + ".html")).write_text(page)
cards = "".join(f'<a class="report-card" href="{E(r["slug"])}.html"><div class="eyebrow">SEO / GEO / CONTENT</div><h2>{E(r["display_title"])}</h2><p>{E(r["article"]["title"])}</p><div class="card-bottom"><span>证据覆盖率 <b>{E(r["framework_result"].get("evidence_coverage", "—"))}%</b></span><span>查看报告 →</span></div></a>' for r in reports)
index = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>GARVEE SEO / GEO 分析报告</title><link rel="stylesheet" href="style.css"></head><body><header><a class="brand" href="index.html">GARVEE <span>SEO / GEO 分析报告</span></a><span class="edition">2026.10 / 冻结审核快照</span></header><main><div class="eyebrow">SEO / GEO / EVIDENCE</div><h1>文章 SEO 与 GEO 分析</h1><p class="subtitle">页面代码、内容可信度和本机语义检索分别呈现，结论附可复核的证据。</p><aside class="notice"><b>两篇公开文章已重新审核。</b>GEO Optimizer、SAGE 向量后端与本机 Codex 真实执行。DataForSEO 外链尚未查询，渲染 DOM、真实 AI 平台引用未测量，报告标记为不完整。证据覆盖率不是质量得分。</aside><div class="report-grid">{cards}</div><p class="section-note">未执行 AI 写作检测或查重。报告只覆盖所列文章及本次冻结材料，不能代表全目录或全站。<a href="https://github.com/igocc/garvee-content-quality-reports">GitHub 仓库 ↗</a></p></main><footer>SEO／GEO 分项状态可追踪 · 非 Google 官方评分 · 非真实 AI 引用率</footer></body></html>'''
(ROOT / "index.html").write_text(index)
print("Generated", len(reports), "frozen article reports")
