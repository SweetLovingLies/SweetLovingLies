"""Builds assets/stats.svg (a pastel 'stats.exe' window) from the GitHub API.
Runs daily in GitHub Actions using the built-in GITHUB_TOKEN. No third-party service needed."""
import json, os, urllib.request, html

USER = os.environ.get("GH_USER", "SweetLovingLies")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
F = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Courier New',monospace"
INK = "#3b2a66"

def api(url, data=None):
    req = urllib.request.Request(url, data=data)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN: req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

repos, page = [], 1
while True:
    chunk = api(f"https://api.github.com/users/{USER}/repos?per_page=100&page={page}&type=owner")
    repos += chunk
    if len(chunk) < 100: break
    page += 1
repos = [r for r in repos if not r["fork"]]
stars = sum(r["stargazers_count"] for r in repos)
langs = {}
for r in repos:
    try:
        for k, v in api(r["languages_url"]).items(): langs[k] = langs.get(k, 0) + v
    except Exception: pass

contribs = None
if TOKEN:
    q = '{user(login:"%s"){contributionsCollection{contributionCalendar{totalContributions}}}}' % USER
    try:
        res = api("https://api.github.com/graphql", json.dumps({"query": q}).encode())
        contribs = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    except Exception: pass

# ---- draw ----
W, H = 400, 176
COLORS = ["#ff8fd0", "#b39bff", "#7fe9ff", "#ffe08a", "#ffb3e1"]
total = sum(langs.values()) or 1
top = sorted(langs.items(), key=lambda kv: -kv[1])[:4]
bar, legend, x = "", "", 24
for i, (name, n) in enumerate(top):
    w = max(6, 352 * n / total)
    bar += f'<rect x="{x:.1f}" y="128" width="{w:.1f}" height="10" fill="{COLORS[i]}"/>'
    x += w
    legend += f'<circle cx="{28+i*88}" cy="156" r="4" fill="{COLORS[i]}"/><text x="{36+i*88}" y="160" font-family="{F}" font-size="11" fill="{INK}">{html.escape(name)} {100*n/total:.0f}%</text>'

def row(y, label, val):
    return (f'<text x="24" y="{y}" font-family="{F}" font-size="13" fill="{INK}">{label}</text>'
            f'<text x="376" y="{y}" text-anchor="end" font-family="{F}" font-size="14" font-weight="700" fill="#d6349b">{val}</text>')

rows = row(72, "✧ contributions (last year)", contribs if contribs is not None else "-")
rows += row(96, "★ stars earned", stars)
rows += row(118, "▣ public repos", len(repos))

def buttons(w):
    x, out = w - 14, ""
    for g in ("x", "box", "min"):
        x -= 26
        out += f'<rect x="{x}" y="7" width="22" height="22" rx="4" fill="#fff" stroke="#b69cff" stroke-width="1.5"/>'
        c = x + 11
        if g == "x": out += f'<path d="M{c-4} 13L{c+4} 21M{c+4} 13L{c-4} 21" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
        if g == "box": out += f'<rect x="{c-4}" y="14" width="8" height="8" rx="1" fill="none" stroke="{INK}" stroke-width="2"/>'
        if g == "min": out += f'<path d="M{c-4} 21H{c+4}" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
    return out

def dots():
    return "".join(f'<circle cx="{22+i*19}" cy="20" r="6" fill="{c}" stroke="#7b5cff" stroke-opacity=".45"/>' for i, c in enumerate(("#ffb3e1", "#ffe08a", "#9fe8ff")))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub stats">
<defs><linearGradient id="tb" x1="0" x2="1"><stop offset="0" stop-color="#ffb3e1"/><stop offset=".55" stop-color="#b9a2ff"/><stop offset="1" stop-color="#9fe8ff"/></linearGradient>
<clipPath id="clip"><rect x="2" y="2" width="{W-8}" height="{H-8}" rx="10"/></clipPath></defs>
<rect x="6" y="6" width="{W-8}" height="{H-8}" rx="10" fill="#7b5cff" fill-opacity=".35"/>
<rect x="2" y="2" width="{W-8}" height="{H-8}" rx="10" fill="#f6ecff" stroke="#b69cff" stroke-width="2"/>
<g clip-path="url(#clip)"><rect x="2" y="2" width="{W-8}" height="36" fill="url(#tb)"/><line x1="2" x2="{W-6}" y1="38" y2="38" stroke="#b69cff" stroke-width="2"/></g>
{dots()}<text x="82" y="25" font-family="{F}" font-size="14" font-weight="700" fill="{INK}">ʚɞ stats.exe</text>
<g transform="translate(-6,2)">{buttons(W)}</g>
{rows}
<rect x="24" y="128" width="352" height="10" rx="5" fill="#e4d6ff"/>
<g clip-path="url(#bar)"><clipPath id="bar"><rect x="24" y="128" width="352" height="10" rx="5"/></clipPath>{bar}</g>
{legend}
<text x="376" y="160" text-anchor="end" font-family="{F}" font-size="12" fill="#d6349b">₍ᐢ⑅ᐢ₎</text>
</svg>'''
os.makedirs("assets", exist_ok=True)
open("assets/stats.svg", "w").write(svg)
print("repos", len(repos), "stars", stars, "contribs", contribs, "langs", top)
