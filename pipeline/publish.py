#!/usr/bin/env python3
"""
Publish dashboards to docs/ for GitHub Pages.

Scans projects/*/reports/dashboard.html, copies each into
docs/<project-slug>/index.html, and generates a landing page at docs/index.html.

Usage:
    python pipeline/publish.py
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PROJECTS_DIR = ROOT / "projects"
DOCS_DIR = ROOT / "docs"


def load_project_meta(project_dir: Path) -> dict | None:
    config_path = project_dir / "config.yaml"
    dashboard_path = project_dir / "reports" / "dashboard.html"
    if not config_path.exists() or not dashboard_path.exists():
        return None

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    hypothesis = cfg.get("narrative_hypothesis", "").strip()
    teaser = hypothesis[:200].rsplit(" ", 1)[0] + "..." if len(hypothesis) > 200 else hypothesis

    return {
        "slug": cfg["name"],
        "title": cfg.get("title", cfg["name"]),
        "teaser": teaser,
        "dashboard_path": dashboard_path,
        "size_mb": dashboard_path.stat().st_size / (1024 * 1024),
    }


def copy_dashboards(projects: list[dict]) -> None:
    for p in projects:
        dest = DOCS_DIR / p["slug"]
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p["dashboard_path"], dest / "index.html")
        print(f"  + {p['slug']}/index.html ({p['size_mb']:.1f} MB)")


def make_project_card(p: dict) -> str:
    return f"""      <a href="{p['slug']}/" class="card">
        <div class="card-body">
          <h3>{p['title']}</h3>
          <p>{p['teaser']}</p>
        </div>
        <div class="card-footer">
          <span class="badge">Interactive Dashboard</span>
          <span class="arrow">&rarr;</span>
        </div>
      </a>"""


def generate_landing_page(projects: list[dict]) -> str:
    cards = "\n".join(make_project_card(p) for p in projects)
    year = datetime.now().year

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>antimatter &middot; Data Adventures</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg:      #0b0f1a;
      --bg2:     #10141f;
      --border:  rgba(255,255,255,0.06);
      --card:    rgba(255,255,255,0.02);
      --card-h:  rgba(255,255,255,0.05);
      --rose:    #f43f5e;
      --amber:   #f59e0b;
      --sky:     #38bdf8;
      --emerald: #34d399;
      --violet:  #a78bfa;
      --text:    #e2e8f0;
      --muted:   #94a3b8;
      --dim:     #64748b;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      line-height: 1.7;
      -webkit-font-smoothing: antialiased;
    }}

    /* ---- HERO ---- */
    .hero {{
      min-height: 60vh;
      display: flex; align-items: center; justify-content: center;
      text-align: center; padding: 6rem 2rem 4rem;
    }}
    .hero-inner {{ max-width: 720px; }}
    .wordmark {{
      font-size: clamp(2.2rem, 5vw, 3.2rem);
      font-weight: 700; color: #fff;
      letter-spacing: -0.02em;
      margin-bottom: 0.3rem;
    }}
    .wordmark span {{ color: var(--rose); }}
    .tagline {{
      font-size: clamp(1rem, 2.2vw, 1.25rem);
      color: var(--muted); font-weight: 400;
      margin-bottom: 2rem;
    }}
    .intro {{
      font-size: 0.95rem; color: var(--dim);
      max-width: 560px; margin: 0 auto;
      line-height: 1.85;
    }}
    .intro strong {{ color: var(--muted); font-weight: 500; }}

    /* ---- SECTION ---- */
    .section {{
      max-width: 960px; margin: 0 auto;
      padding: 0 2rem 6rem;
    }}
    .section-label {{
      font-size: 0.7rem; font-weight: 600;
      letter-spacing: 0.12em; text-transform: uppercase;
      color: var(--dim); margin-bottom: 1.5rem;
      padding-top: 2rem;
      border-top: 1px solid var(--border);
    }}

    /* ---- CARDS ---- */
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 1.5rem;
    }}
    .card {{
      display: flex; flex-direction: column;
      justify-content: space-between;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.8rem 1.8rem 1.4rem;
      text-decoration: none; color: inherit;
      transition: background 0.2s, border-color 0.2s, transform 0.2s;
    }}
    .card:hover {{
      background: var(--card-h);
      border-color: rgba(255,255,255,0.12);
      transform: translateY(-2px);
    }}
    .card h3 {{
      font-size: 1.1rem; font-weight: 600; color: #fff;
      line-height: 1.35; margin-bottom: 0.7rem;
    }}
    .card p {{
      font-size: 0.85rem; color: var(--muted);
      line-height: 1.75; flex-grow: 1;
    }}
    .card-footer {{
      display: flex; align-items: center;
      justify-content: space-between;
      margin-top: 1.4rem; padding-top: 1rem;
      border-top: 1px solid var(--border);
    }}
    .badge {{
      font-size: 0.68rem; font-weight: 500;
      letter-spacing: 0.06em; text-transform: uppercase;
      color: var(--emerald);
      background: rgba(52,211,153,0.08);
      padding: 0.3rem 0.7rem; border-radius: 4px;
    }}
    .arrow {{
      font-size: 1.2rem; color: var(--dim);
      transition: color 0.15s, transform 0.15s;
    }}
    .card:hover .arrow {{
      color: var(--rose);
      transform: translateX(3px);
    }}

    /* ---- EMPTY STATE ---- */
    .empty {{
      text-align: center; padding: 3rem 1rem;
      color: var(--dim); font-size: 0.9rem;
    }}

    /* ---- FOOTER ---- */
    footer {{
      border-top: 1px solid var(--border);
      padding: 2rem; text-align: center;
      font-size: 0.72rem; color: var(--dim);
    }}
    footer a {{ color: var(--sky); text-decoration: none; }}

    @media (max-width: 480px) {{
      .cards {{ grid-template-columns: 1fr; }}
      .card {{ padding: 1.4rem; }}
    }}
  </style>
</head>
<body>

<section class="hero">
  <div class="hero-inner">
    <div class="wordmark">anti<span>matter</span></div>
    <p class="tagline">Stories in Data</p>
    <p class="intro">
      Independent data investigations that dig beneath the headline numbers.
      We pull from <strong>public sources</strong> &mdash; Census, FRED, BLS, World Bank &mdash;
      and build interactive dashboards that let the data speak for itself.
      <strong>No spin. No agenda. Just the numbers.</strong>
    </p>
  </div>
</section>

<div class="section">
  <div class="section-label">Published Investigations</div>
  <div class="cards">
{cards if cards.strip() else '    <div class="empty">No dashboards published yet. Run a project through the pipeline first.</div>'}
  </div>
</div>

<footer>
  <p>&copy; {year} antimatter &middot; All data sourced from public government databases</p>
  <p style="margin-top:0.3rem;">
    Built with Python, Plotly &amp; too much coffee &middot;
    <a href="https://github.com/unstableantimatter/data-adventures">Source</a>
  </p>
</footer>

</body>
</html>"""


def main():
    print("Publishing dashboards to docs/...")

    project_dirs = sorted(PROJECTS_DIR.iterdir())
    projects = []
    for d in project_dirs:
        if not d.is_dir():
            continue
        meta = load_project_meta(d)
        if meta:
            projects.append(meta)

    if not projects:
        print("  No publishable dashboards found.")
        return

    print(f"  Found {len(projects)} dashboard(s):\n")
    copy_dashboards(projects)

    landing = generate_landing_page(projects)
    index_path = DOCS_DIR / "index.html"
    DOCS_DIR.mkdir(exist_ok=True)
    index_path.write_text(landing)
    print(f"\n  + index.html (landing page, {len(projects)} cards)")
    print(f"\nDone. docs/ ready for GitHub Pages.")


if __name__ == "__main__":
    main()
