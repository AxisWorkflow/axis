#!/usr/bin/env python3
"""Axis ^status: a read-only summary of the project's canonical records.

Optional accelerator for `_Axis/Commands/status.md`. It reads project records,
never writes them, and prints a terminal summary (default), JSON, or a static
branded web page under `_Temp/status/`. Without Python the Agent composes the
same summary by hand from the same records.
"""
import argparse, datetime as dt, html, json, os, re, shutil, subprocess, sys
from pathlib import Path

sys.dont_write_bytecode = True
TS = re.compile(r'^\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3}Z\.md$')


def read(p):
    try:
        return Path(p).read_text(encoding='utf-8', errors='replace')
    except OSError:
        return ''


def records(root, *dirs):
    """Timestamp-named record files, newest first, across the given folders."""
    out = []
    for d in dirs:
        p = root / d
        if p.is_dir() and not p.is_symlink():
            out += [f for f in p.iterdir() if TS.match(f.name) and f.is_file()]
    return sorted(out, key=lambda f: f.name, reverse=True)


def subject(f):
    for line in read(f).splitlines():
        s = line.strip().lstrip('#').strip()
        return re.sub(r'^(Follow-Up|Reminder|Request): ', '', s)
    return ''


def fields(text):
    return {m.group(1): m.group(2).strip() for m in re.finditer(r'^([a-z][a-z-]*): ?(.*)$', text, re.M)}


def when(name):
    try:
        return dt.datetime.strptime(name[:23], '%Y.%m.%d.%H.%M.%S.%f').replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return None


def age(t, now):
    if not t:
        return ''
    s = (now - t).total_seconds()
    if s < 3600:
        return f'{max(1, int(s // 60))}m ago'
    if s < 172800:
        return f'{int(s // 3600)}h ago'
    return f'{int(s // 86400)}d ago'


def blocks(text, level='## '):
    """Split a Markdown index into (heading, body) blocks at the given heading level."""
    out, head, body = [], None, []
    for line in text.splitlines():
        if line.startswith(level) and not line.startswith(level + '#'):
            if head is not None:
                out.append((head, '\n'.join(body)))
            head, body = line[len(level):].strip(), []
        elif head is not None:
            body.append(line)
    if head is not None:
        out.append((head, '\n'.join(body)))
    return out


def first_paragraph(text, after=None):
    seen = after is None
    for para in re.split(r'\n\s*\n', text):
        p = para.strip()
        if not seen:
            seen = p.startswith(after)
            continue
        if p and not p.startswith(('#', '>', '<!--', '|', '-', '*')) and '{{' not in p:
            p = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', p)
            return re.sub(r'\s+', ' ', p.replace('**', '').replace('`', ''))
    return ''


def collect(root, detail):
    now = dt.datetime.now(dt.timezone.utc)
    ax = root / '_Axis'
    project = read(ax / 'PROJECT.md')
    name = (re.findall(r'^# Project:\s*(.+)$', project, re.M) or ['Not set'])[0].strip()
    if '{{' in name:
        name = 'Not set'
    version = (re.findall(r'^current-version: (\S+)$', read(ax / 'CHANGELOG.md'), re.M) or ['Unavailable'])[0]
    plan = read(ax / 'PLAN.md')
    direction = first_paragraph(plan, after='## ') or 'No Plan written yet.'
    tasks = []
    for head, body in blocks(read(ax / 'TASKS.md')):
        f = fields(body)
        if '{{' in head + body or 'status' not in f:
            continue
        tasks.append({'name': head, 'label': f.get('label', ''), 'status': f.get('status', ''),
                      'updated': f.get('updated', ''), 'initiative': f.get('initiative', '')})
    count = {s: sum(t['status'] == s for t in tasks) for s in ('Active', 'Planned', 'Blocked', 'Completed', 'Cancelled')}
    inits = []
    for head, body in blocks(read(ax / 'INITIATIVES.md')):
        f = fields(body)
        if 'status' in f and '{{' not in head + body:
            inits.append({'key': head, 'name': f.get('name', head), 'status': f['status'], 'phase': f.get('phase', '')})
    fus = []
    for f in records(root, '_Axis/Followups'):
        fl = fields(read(f))
        fus.append({'subject': subject(f), 'due': fl.get('due', ''), 'id': f.name[:-3]})
    rem = []
    for f in records(root, '_Axis/Reminders'):
        fl = fields(read(f))
        if fl.get('status', 'open') == 'open':
            rem.append({'subject': subject(f), 'due': fl.get('due', ''), 'id': f.name[:-3]})
    rem.sort(key=lambda r: r['due'] or '~')
    logs = [{'subject': subject(f), 'age': age(when(f.name), now)} for f in records(root, '_Axis/Logs')[:12 if detail == 'full' else 4]]
    snaps = records(root, '_Axis/Snapshots')
    reviews = records(root, '_Axis/Reviews', '_Axis/Status')
    agents = []
    ad = ax / 'Agents'
    for f in (ad.iterdir() if ad.is_dir() else []):
        if f.suffix == '.md' and TS.match(f.name) and not f.with_suffix('.kill').exists():
            fresh = now.timestamp() - f.stat().st_mtime < 3600
            if fresh:
                agents.append(subject(f))
    git = ''
    if shutil.which('git') and (root / '.git').exists():
        try:
            br = subprocess.run(['git', '-C', str(root), 'branch', '--show-current'], capture_output=True, text=True, timeout=5).stdout.strip()
            dirty = subprocess.run(['git', '-C', str(root), 'status', '--porcelain'], capture_output=True, text=True, timeout=10).stdout.strip()
            git = f"{br or 'detached'}{', uncommitted changes' if dirty else ', clean'}"
        except (OSError, subprocess.SubprocessError):
            git = ''
    def n(d):
        p = root / d
        return len([f for f in p.iterdir() if TS.match(f.name)]) if p.is_dir() else 0
    active = [t for t in tasks if t['status'] == 'Active']
    blocked = [t for t in tasks if t['status'] == 'Blocked']
    data = {
        'generated': now.strftime('%Y-%m-%d %H:%M UTC'), 'project': name, 'version': version, 'folder': str(root),
        'direction': direction, 'tasks': count, 'active': active, 'blocked': blocked,
        'initiatives': [i for i in inits if detail == 'full' or i['status'] not in ('Completed', 'Cancelled')],
        'followups': fus, 'reminders': rem[:10], 'logs': logs,
        'snapshot': {'subject': subject(snaps[0]), 'age': age(when(snaps[0].name), now)} if snaps else None,
        'review': {'subject': subject(reviews[0]), 'age': age(when(reviews[0].name), now), 'path': str(reviews[0].relative_to(root))} if reviews else None,
        'agents': agents, 'git': git, 'root': str(root),
        'counts': {'Notes': n('_Axis/Notes'), 'Ideas': n('_Axis/Ideas'), 'Requests': n('_Axis/Requests'), 'Logs': n('_Axis/Logs')},
        'detail': detail,
    }
    if detail == 'full':
        data['recent_completed'] = [t for t in tasks if t['status'] == 'Completed'][-8:]
        data['plan_sections'] = [h for h, _ in blocks(plan)]
    return data


def clip(s, w):
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)
    return s if len(s) <= w else s[:w - 1] + '…'


def heading_sgr():
    """Brand terminal rule (tokens.json > terminal): headings bold, brand blue chosen by background, bold only when unknown."""
    theme = os.environ.get('AXIS_THEME', '').lower()
    if theme == 'plain':
        return None
    if theme not in ('light', 'dark'):
        fgbg = os.environ.get('COLORFGBG', '').split(';')[-1]
        theme = 'dark' if fgbg in ('0', '1', '2', '3', '4', '5', '6', '8') else 'light' if fgbg in ('7', '15') else ''
    return {'light': '1;38;2;47;86;201', 'dark': '1;38;2;143;168;245'}.get(theme, '1')


def text(d, width, color):
    sgr = heading_sgr() if color else None
    A = (lambda s: f'\033[{sgr}m{s}\033[0m') if sgr else (lambda s: s)
    B = A
    M = lambda s: s
    # Header and summary block (User design, 2026-09-30): spaced title between dividers, then one block of
    # "Label:" rows in aligned columns. Git stays in the background, so it is not shown.
    rule = '━' * 40
    out = [rule, '  ' + B('A X I S   P R O J E C T  S T A T U S'), rule, '']
    t = d['tasks']
    home = os.path.expanduser('~'); path = d['root']
    path = '~' + path[len(home):] if path == home or path.startswith(home + '/') else path
    left = [('Project', d['project']), ('Path', path), ('Version', d['version']), ('As of', d['generated']),
            ('Tasks active', t['Active']), ('Tasks planned', t['Planned']), ('Tasks blocked', t['Blocked']), ('Tasks done', t['Completed'])]
    right = {4: ('Follow-Ups', len(d['followups'])), 5: ('Reminders', len(d['reminders'])), 6: ('Agents live', len(d['agents']))}
    lw = max(len(k) for k, _ in left) + 1; rw = max(len(k) for k, _ in right.values()) + 1
    cw = max(lw + 2 + len(str(left[i][1])) for i in right)
    for i, (k, v) in enumerate(left):
        cell = f"{(k + ':').ljust(lw)}  {v}"
        if i in right:
            rk, rv = right[i]
            cell = cell.ljust(cw) + f"    {(rk + ':').ljust(rw)}  {rv}"
        out.append('  ' + cell)
    out += ['', B('  Direction'), *wrap(d['direction'], width - 4, 4 if d['detail'] == 'full' else 3)]
    if d['active'] or d['blocked']:
        out += ['', B('  Now')]
        for x in d['active'][:8 if d['detail'] == 'full' else 4]:
            out.append(f"    {A('>')} {clip(x['name'] + ' - ' + x['label'], width - 8)}")
        for x in d['blocked'][:6 if d['detail'] == 'full' else 3]:
            out.append(f"    {A('!')} {clip('Blocked: ' + x['name'] + ' - ' + x['label'], width - 8)}")
    if d['initiatives']:
        out += ['', B('  Initiatives')]
        for i in d['initiatives'][:8]:
            out.append(f"    {clip(i['name'] + ' (' + i['status'] + (', ' + i['phase'] if i['phase'] and i['phase'] != i['status'] else '') + ')', width - 6)}")
    if d['followups']:
        out += ['', B('  Waiting on you')]
        for f in d['followups'][:5]:
            out.append(f"    - {clip(f['subject'] + (' (due ' + f['due'] + ')' if f['due'] and f['due'] != 'N/A' else ''), width - 8)}")
    if d['reminders']:
        out += ['', B('  Reminders')]
        for r in d['reminders'][:3]:
            out.append(f"    - {clip(r['subject'] + (' - ' + r['due'] if r['due'] else ''), width - 8)}")
    out += ['', B('  Recent')]
    if not d['logs']:
        out.append(M('    No Logs yet.'))
    for l in d['logs']:
        out.append(f"    {M(l['age'].rjust(8))}  {clip(l['subject'], width - 16)}")
    tail = []
    if d['snapshot']:
        tail.append(f"last Snapshot {d['snapshot']['age']}")
    if d['review']:
        tail.append(f"last Review {d['review']['age']}")
    if tail:
        out += ['', M('  ' + '; '.join(tail))]
    if d['detail'] == 'full':
        if d.get('recent_completed'):
            out += ['', B('  Recently completed')]
            out += [f"    - {clip(x['name'], width - 8)}" for x in d['recent_completed']]
        c = d['counts']
        out += ['', M(f"  Records: {c['Logs']} Logs, {c['Notes']} Notes, {c['Ideas']} Ideas, {c['Requests']} Requests waiting")]
    out += ['', rule]
    return '\n'.join(out)


def wrap(s, w, maxlines):
    words, lines, cur = s.split(), [], ''
    for word in words:
        if len(cur) + len(word) + 1 > w:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + ' ' + word).strip()
    if cur:
        lines.append(cur)
    if len(lines) > maxlines:
        lines = lines[:maxlines]
        lines[-1] = lines[-1][:w - 1] + '…'
    return ['    ' + l for l in lines]


FALLBACK_CSS = """body{margin:0;background:#FFFFFF;color:#0B1220;font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
code{font-family:ui-monospace,Menlo,Consolas,monospace}"""
PAGE_CSS = """.wrap{max-width:1080px;margin:0 auto;padding:32px 24px 48px}
body{background:var(--axis-bg,#FFFFFF);color:var(--axis-fg,#0B1220)}
header.band{background:var(--axis-ink,#0B1220);color:var(--axis-navy-text,#DCE4F5);padding:28px 0}
header .wrap{padding-top:0;padding-bottom:0;display:flex;align-items:center;gap:20px;flex-wrap:wrap}
header img{height:40px}
header h1{margin:0;font-size:28px;color:#FFFFFF;letter-spacing:-0.02em}
header .meta{margin-left:auto;font-family:var(--axis-font-mono,monospace);font-size:13px;color:var(--axis-navy-muted,#B7C1D3)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:24px 0}
.stat{background:var(--axis-band,#EEF2F9);border-radius:var(--axis-radius,14px);padding:14px 18px}
.stat strong{display:block;font-size:30px;color:var(--axis-link,#2F56C9);line-height:1.2}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.card{background:var(--axis-raised,#FFFFFF);border:1px solid var(--axis-border,#D5DCE8);border-radius:var(--axis-radius,14px);padding:18px 20px}
.card h2{font-size:15px;margin:0 0 8px;font-family:var(--axis-font-mono,monospace);text-transform:uppercase;letter-spacing:.08em;color:var(--axis-fg-muted,#5B6472)}
.card ul{margin:0;padding-left:18px}.card li{margin:4px 0}
.muted{color:var(--axis-fg-muted,#5B6472)}
.lede{font-size:19px;margin:0 0 8px}
footer{margin-top:40px;font-size:14px;color:var(--axis-fg-muted,#5B6472);border-top:1px solid var(--axis-border,#D5DCE8);padding-top:14px}"""


def page(d, root, out):
    e = html.escape
    brand = next((b for b in (root / '_Axis' / 'Branding', root / 'Branding') if (b / 'css' / 'axis-brand.css').is_file()), root / '_Axis' / 'Branding')
    rel = os.path.relpath(brand, out.parent).replace(os.sep, '/')
    has = (brand / 'css' / 'axis-brand.css').is_file()
    head = (f'<link rel="stylesheet" href="{rel}/css/axis-brand.css"><link rel="icon" href="{rel}/favicon/favicon.svg" type="image/svg+xml">'
            if has else f'<style>{FALLBACK_CSS}</style>')
    logo = f'<img src="{rel}/svg/logo/logo-reversed.svg" alt="Axis Workflow" height="40">' if has else '<strong>Axis Workflow</strong>'
    def li(items):
        return ''.join(f'<li>{e(x)}</li>' for x in items) or '<li class="muted">None</li>'
    t = d['tasks']
    stats = [(t['Active'], 'active tasks'), (t['Planned'], 'planned'), (t['Blocked'], 'blocked'), (t['Completed'], 'completed'),
             (len(d['followups']), 'waiting on you'), (len(d['reminders']), 'reminders'), (len(d['agents']), 'agents live')]
    cards = [
        ('Now', li([f"{x['name']} - {clip(x['label'], 140)}" for x in d['active']] + [f"Blocked: {x['name']} - {clip(x['label'], 120)}" for x in d['blocked']])),
        ('Initiatives', li([f"{i['name']} ({i['status']}{', ' + i['phase'] if i['phase'] and i['phase'] != i['status'] else ''})" for i in d['initiatives']])),
        ('Waiting on you', li([f['subject'] + (f" (due {f['due']})" if f['due'] and f['due'] != 'N/A' else '') for f in d['followups']])),
        ('Reminders', li([r['subject'] + (' - ' + r['due'] if r['due'] else '') for r in d['reminders']])),
        ('Recent activity', li([f"{l['age']}: {l['subject']}" for l in d['logs']])),
    ]
    if d['detail'] == 'full' and d.get('recent_completed'):
        cards.append(('Recently completed', li([x['name'] for x in d['recent_completed']])))
    last = '; '.join(filter(None, [f"last Snapshot {d['snapshot']['age']}" if d['snapshot'] else '',
                                   f"last Review {d['review']['age']}" if d['review'] else '']))
    body = (f'<header class="band"><div class="wrap">{logo}<h1>{e(d["project"])}</h1>'
            f'<div class="meta">Version {e(d["version"])} · {e(d["generated"])}</div></div></header>'
            f'<main class="wrap"><p class="axis-eyebrow">Project status</p><p class="lede">{e(clip(d["direction"], 600))}</p>'
            f'<div class="stats">' + ''.join(f'<div class="stat"><strong>{v}</strong>{e(k)}</div>' for v, k in stats) + '</div>'
            f'<div class="grid">' + ''.join(f'<section class="card"><h2>{e(h)}</h2><ul>{b}</ul></section>' for h, b in cards) + '</div>'
            f'<p class="muted">{e(last)}</p>'
            '<footer>A snapshot of this project\'s own records, generated by <code>^status</code>; it does not refresh. '
            'For the live view run <code>^dashboard</code>; for a dated report run <code>^review</code>.<br>'
            'Axis Workflow&trade; is free and open source (MIT License), from SimAxis - training and consulting at simaxis.ai.</footer></main>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(d["project"])} - Axis Workflow status</title>{head}<style>{PAGE_CSS}</style></head>'
            f'<body class="axis-root">{body}</body></html>\n')


def main():
    ap = argparse.ArgumentParser(description='Read-only Axis project status.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--format', choices=('text', 'html', 'json'), default='text')
    ap.add_argument('--detail', choices=('short', 'full'), default='short')
    ap.add_argument('--width', type=int, default=0)
    ap.add_argument('--color', choices=('auto', 'always', 'never'), default='auto')
    a = ap.parse_args()
    root = Path(a.root).resolve()
    if not (root / '_Axis').is_dir():
        print('status: no _Axis/ folder under --root', file=sys.stderr)
        return 2
    d = collect(root, a.detail)
    if a.format == 'json':
        print(json.dumps(d, indent=1, default=str))
    elif a.format == 'html':
        out = root / '_Temp' / 'status' / 'index.html'
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page(d, root, out), encoding='utf-8')
        print(out)
    else:
        width = a.width or min(shutil.get_terminal_size((80, 24)).columns, 100)
        term = os.environ.get('TERM', '')
        color = a.color == 'always' or (a.color == 'auto' and sys.stdout.isatty() and term not in ('', 'dumb') and not os.environ.get('NO_COLOR'))
        print(text(d, width, color))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
