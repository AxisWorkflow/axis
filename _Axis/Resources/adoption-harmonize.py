#!/usr/bin/env python3
"""Best-effort target-convention scan with exact, recoverable optional repair units.

Only a verified adoption engine supplies authority and calls apply. No source text
is executed. Unknown content remains in place; residuals are warnings, not gates.
"""
import datetime
import subprocess
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import urllib.parse
import uuid

CONVENTIONS = 'axis-layout/v3.08'
ROOTS = ('_Axis', '_Memos', '_Wiki', '_Dev')
FAMILIES = {'Tasks','Ideas','Notes','Logs','Snapshots','CX','Audit','Reviews','Status','Supervision','Followups','Reminders','Messages','Teams','Jobs','Schedules'}
ID = re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\Z')
PRIVATE = {'Secrets','Agents','Flags','Tracking','.git','.codex','.claude','.gemini'}
MAX_TEXT = 1024 * 1024


def digest(raw): return hashlib.sha256(raw).hexdigest()


def valid_id(value):
    if not isinstance(value,str) or not ID.fullmatch(value):return False
    try:datetime.datetime.strptime(value,'%Y.%m.%d.%H.%M.%S.%fZ');return True
    except ValueError:return False


def recovery(root,journal,op,side):
    if side=='after' and op['after']==op['before']:return recovery(root,journal,op,'before')
    commit=op.get('git_before') if side=='before' else None
    if commit:
        if not re.fullmatch('[0-9a-f]{40,64}',commit):raise ValueError('invalid Git recovery checkpoint')
        q=subprocess.run(['git','-C',str(root),'show',commit+':'+op['source']],capture_output=True,timeout=30)
        if q.returncode:raise ValueError('Git recovery checkpoint unavailable')
        data=q.stdout
    else:data=(journal/(str(op['index'])+'.'+side)).read_bytes()
    if digest(data)!=op[side]['sha256'] or len(data)!=op[side]['bytes']:raise ValueError('repair recovery input changed')
    return data


def checkpoint(root):
    try:
        q=subprocess.run(['git','-C',str(root),'rev-parse','--show-toplevel'],capture_output=True,timeout=10)
        if q.returncode or Path(q.stdout.decode().strip()).resolve()!=root.resolve():return None
        q=subprocess.run(['git','-C',str(root),'rev-parse','--verify','HEAD^{commit}'],capture_output=True,timeout=10)
        return q.stdout.decode().strip() if q.returncode==0 else None
    except (OSError,ValueError,subprocess.SubprocessError):return None



def safe(root, name):
    parts = name.split('/')
    if parts[0] not in ROOTS or any(p in ('', '.', '..') or p in PRIVATE or p.endswith(('_U','_X')) for p in parts):
        raise ValueError('repair path outside allowed adoption content')
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink(): raise ValueError('linked repair path')
        if path.parent.is_dir() and any(p.name.casefold()==part.casefold() and p.name!=part for p in path.parent.iterdir()):raise ValueError('case alias repair path')
    return path


def identity(path):
    if not path.exists(): return None
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1: raise ValueError('nonordinary repair file')
    raw = path.read_bytes()
    return {'sha256':digest(raw), 'bytes':len(raw), 'mode':stat.S_IMODE(info.st_mode)}


def syncdir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def once(path, value):
    data = (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    with path.open('xb') as out: out.write(data);out.flush();os.fsync(out.fileno())
    syncdir(path.parent)
    if path.read_bytes()!=data: raise ValueError('repair journal readback failed')


def scan_entries(root, folder, journal=None, guard=lambda:None):
    """One directory is one resumable metadata chunk; contents are never cached.

    Recheck child stat data before reuse, so edits inside an unchanged directory
    do not make a stale size/link classification authoritative for repair.
    """
    name=folder.relative_to(root).as_posix()
    cached=journal/('scan-'+digest(name.encode())+'.json') if journal else None
    if cached and cached.exists():
        try:
            value=json.loads(cached.read_text())
            info=folder.lstat();token=[info.st_dev,info.st_ino,info.st_mtime_ns]
            if value['path']==name and value['token']==token:
                entries=[]
                for child in value['names']:
                    if not isinstance(child,str) or child in ('','.','..') or '/' in child:raise ValueError('invalid scan chunk')
                    entries.append(folder/child)
                return entries
        except (OSError,ValueError,KeyError,TypeError):pass
    entries=sorted(folder.iterdir())
    if cached:
        info=folder.lstat();value={'schema':1,'path':name,'token':[info.st_dev,info.st_ino,info.st_mtime_ns],'names':[p.name for p in entries]}
        guard();journal.mkdir(exist_ok=True)
        pending=journal/'scan.pending'
        # This scratch file belongs to this serialized adoption, not project data.
        if pending.exists():pending.unlink()
        once(pending,value);guard();os.replace(pending,cached);syncdir(journal)
    return entries


def inventory(root, journal=None, guard=lambda:None):
    """Walk every present root, recording explicit protected/nested/unreadable boundaries."""
    files={};directories=[];residual=[];counts={'files':0,'directories':0,'boundaries':0,'unreadable':0}
    def walk(folder):
        try: entries=scan_entries(root,folder,journal,guard)
        except OSError:
            counts['unreadable']+=1;residual.append({'path':folder.relative_to(root).as_posix(),'reason':'unreadable subtree; left in place'});return
        for path in entries:
            name=path.relative_to(root).as_posix()
            if path.name in PRIVATE or path.name.endswith(('_U','_X')):
                counts['boundaries']+=1;residual.append({'path':name,'reason':'protected structural boundary; contents intentionally unscanned'});continue
            try:
                info=path.lstat()
                if stat.S_ISLNK(info.st_mode):
                    counts['boundaries']+=1;residual.append({'path':name,'reason':'symlink boundary; left in place'});continue
                if stat.S_ISDIR(info.st_mode):
                    counts['directories']+=1;directories.append(name)
                    if (path/'_Axis/PROJECT.md').is_file():
                        counts['boundaries']+=1;residual.append({'path':name,'reason':'independent nested project; contents intentionally unscanned'});continue
                    walk(path)
                elif stat.S_ISREG(info.st_mode):
                    counts['files']+=1
                    files[name]={'bytes':info.st_size,'mode':stat.S_IMODE(info.st_mode),'links':info.st_nlink}
                else:
                    counts['boundaries']+=1;residual.append({'path':name,'reason':'special file; left in place'})
            except OSError:
                counts['unreadable']+=1;residual.append({'path':name,'reason':'unreadable entry; left in place'})
    present=[]
    for name in ROOTS:
        path=root/name
        if path.is_symlink():residual.append({'path':name,'reason':'linked root; left in place'});counts['boundaries']+=1
        elif path.is_dir():present.append(name);walk(path)
    return {'roots':present,'files':files,'directories':directories,'counts':counts,'residual':residual}


def identity_available(root, value):
    """Use the shipped full collision domain, including Agents and cold IDs.

    This only inspects record names/catalog metadata. An unavailable archive or
    malformed domain is uncertainty, never permission to reuse an identity.
    """
    startup=None
    try:
        spec=importlib.util.spec_from_file_location('axis_adoption_identity',root/'_Axis/Resources/startup-state.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        startup=module.Startup(root)
        relative,external=module.archive_root(startup)
        if relative is None and external is None:return False
        return not startup.collision(value)
    except Exception:
        return False
    finally:
        if startup is not None:startup.close()


def candidate_moves(root, scan):
    moves={};residual=[];owners={};ids={Path(p).stem for p in scan['files'] if ID.fullmatch(Path(p).stem)}
    for name, info in scan['files'].items():
        if name in scan.get('excluded',[]):continue
        parts=name.split('/');p=Path(name)
        if info['links']!=1 or info['bytes']>MAX_TEXT:continue
        target=None
        # A known old family archive has an unambiguous target convention.
        if len(parts)==4 and parts[:2]==['_Axis','Archive'] and parts[2] in FAMILIES and valid_id(p.stem):
            target='_Axis/'+parts[2]+'/Archive/'+parts[3]
        message_location=parts[0]=='_Axis' and (parts[1]=='Messages' or len(parts)>3 and parts[1:3]==['Archive','Messages'])
        if message_location and p.suffix=='.md':
            try:
                raw=(root/name).read_text()
                formatter=root/'_Axis/Resources/coordination-record.py'
                spec=importlib.util.spec_from_file_location('axis_adopted_record_format',formatter)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                subject,value=module.decode(raw)
                if value.get('schema')!='axis.coordination/v1' or value.get('family')!='Messages' or value.get('subject')!=subject:raise ValueError('schema')
                record_id=value.get('id')
                if not valid_id(record_id) or record_id!=p.stem and (record_id in ids or not identity_available(root,record_id)):raise ValueError('ambiguous identity')
                if str(uuid.UUID(value.get('project')))!=value.get('project') or not valid_id(value.get('created')):raise ValueError('identity')
                issuer=value.get('issuer',{})
                if issuer.get('role') not in {'main','worker','external'} or not valid_id(issuer.get('session')):raise ValueError('issuer')
                if value.get('kind') not in {'request','offer','assignment','question','answer','receipt','result','validation','decision','control','transfer'} or not isinstance(value.get('body'),str):raise ValueError('Message shape')
                if type(value.get('epoch')) is not int or value['epoch']<0 or not valid_id(value.get('expires')) or not isinstance(value.get('data',{}),dict):raise ValueError('Message shape')
                if not all(isinstance(value.get(k),str) and value[k] for k in ('recipient','correlation')):raise ValueError('Message route')
                team=value.get('team')
                if team is not None:
                    if not valid_id(team):raise ValueError('team')
                    team_owners=[root/'_Axis/Teams'/(team+'.md'),root/'_Axis/Teams/Archive'/(team+'.md'),root/'_Axis/Archive/Teams'/(team+'.md')]
                    team_owners=[q for q in team_owners if q.is_file() and not q.is_symlink()]
                    if len(team_owners)!=1:raise ValueError('Team ownership unavailable')
                    _,owner=module.decode(team_owners[0].read_text())
                    if owner.get('family')!='Teams' or owner.get('id')!=team or owner.get('project')!=value['project']:raise ValueError('Team ownership conflict')
                archived='Archive/' if parts[1]=='Archive' or parts[2:3]==['Archive'] else ''
                target='_Axis/Messages/'+archived+('Teams/'+team if team else 'Individual')+'/'+record_id+'.md'
                owners.setdefault(record_id,[]).append((name,target))
            except (OSError,ValueError,StopIteration,TypeError,AttributeError):
                if len(parts)==3 or parts[-2] in {'Individual','Messages'} or len(parts)>3 and parts[-3]=='Teams':residual.append({'path':name,'reason':'unrecognized Message identity/ownership; left in legacy location'})
                target=None
        elif parts[0]=='_Axis' and len(parts)==3 and parts[1] in FAMILIES and p.suffix=='.md':
            if not valid_id(p.stem):
                # Only families whose creation field is their identity can reconstruct a name.
                if parts[1] in {'Tasks','Ideas','Notes','Followups','Reminders'}:
                    try:
                        raw=(root/name).read_text();field='raised' if parts[1]=='Followups' else 'created'
                        found=re.findall(r'^'+field+r': (\S+)\s*$',raw,re.M)
                        if len(found)!=1 or not valid_id(found[0]) or found[0] in ids or not identity_available(root,found[0]):raise ValueError('ambiguous identity')
                        target=str(p.with_name(found[0]+'.md'));ids.add(found[0])
                    except (OSError,ValueError):
                        residual.append({'path':name,'reason':'identity cannot be reconstructed confidently; left in place'})
                else:residual.append({'path':name,'reason':'unsupported malformed record name; left in place'})
        if target and target!=name:
            try:
                safe(root,name);safe(root,target)
                if target in moves.values():raise ValueError('destination collision')
                if (root/target).exists() and identity(root/target)!=identity(root/name):raise ValueError('destination collision')
                moves[name]=target
            except ValueError as exc:residual.append({'path':name,'reason':str(exc)+'; left in place'})
    for source,target in list(moves.items()):
        prefix=source[:-3]+'/'
        support={n:v for n,v in scan['files'].items() if n.startswith(prefix)}
        if any(v['links']!=1 or v['bytes']>MAX_TEXT for v in support.values()) or any(v['path'].startswith(prefix) for v in scan['residual']):
            moves.pop(source);residual.append({'path':source,'reason':'support needs a reviewed large-file move; entire owner retained'});continue
        for name in support:
            dest=target[:-3]+'/'+name[len(prefix):]
            if (root/dest).exists() and identity(root/dest)!=identity(root/name):
                moves.pop(source,None);residual.append({'path':source,'reason':'support destination conflict; entire owner retained'});break
        else:
            for name in support:moves[name]=target[:-3]+'/'+name[len(prefix):]
    # Recover a legacy support folder whose owner already moved successfully.
    # An exact single validated owner is required; never attach orphan bytes by
    # subject text, timestamp proximity or a guessed Team.
    for directory in scan['directories']:
        parts=directory.split('/')
        if len(parts)!=3 or parts[:2]!=['_Axis','Messages'] or not valid_id(parts[-1]):continue
        candidates=owners.get(parts[-1],[])
        if len(candidates)!=1:
            residual.append({'path':directory,'reason':'support ownership unavailable or ambiguous; left in place'});continue
        original,destination=candidates[0]
        if original!=destination or directory==destination[:-3]:continue
        support={n:v for n,v in scan['files'].items() if n.startswith(directory+'/')}
        if any(n.startswith(directory+'/') for n in (v['path'] for v in scan['residual'])):continue
        prepared={}
        for name,info in support.items():
            target=destination[:-3]+name[len(directory):]
            try:
                safe(root,name);safe(root,target)
                if info['links']!=1 or info['bytes']>MAX_TEXT or (root/target).exists() and identity(root/target)!=identity(root/name):raise ValueError('support conflict')
                prepared[name]=target
            except (OSError,ValueError):
                residual.append({'path':directory,'reason':'support conflict or unsupported file; whole folder retained'});break
        else:moves.update(prepared)
    return moves,residual


def rewrite_links(name, text, moves):
    """Only actual Markdown destinations, excluding fenced code and literal history."""
    source=Path(name);new_source=Path(moves.get(name,name));lines=[];fenced=False
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith(('```','~~~')):fenced=not fenced
        if not fenced and not line.startswith(('    ','\t')) and not line.lstrip().startswith('>'):
            def link(match):
                if line[:match.start()].count('`')%2:return match[0]
                destination=match[1];url=urllib.parse.urlsplit(destination.strip('<>'))
                if url.scheme or url.netloc or not url.path or url.path.startswith('/'):return match[0]
                logical=os.path.normpath(str(source.parent/urllib.parse.unquote(url.path)))
                revised=moves.get(logical,logical)
                if logical==revised and source.parent==new_source.parent:return match[0]
                rel=os.path.relpath(revised,str(new_source.parent)).replace(os.sep,'/')
                path=urllib.parse.quote(rel,safe='/._-')
                if url.query:path+='?'+url.query
                if url.fragment:path+='#'+url.fragment
                return ']('+path+')'
            line=re.sub(r'\]\(([^)\n]+)\)',link,line)
        lines.append(line)
    return ''.join(lines)


def prepare(root, scan, journal, guard):
    moves,residual=candidate_moves(root,scan)
    writes={};facts=[]
    for name,info in scan['files'].items():
        if name in scan.get('excluded',[]) or name.startswith(('_Dev/Evidence/','_Dev/Candidate/','_Dev/Artifacts/','_Axis/Updates/','_Axis/Merges/','_Axis/Splits/','_Axis/Repairs/','_Axis/Resources/','_Axis/Rules/','_Axis/Practices/','_Axis/Commands/')):continue
        if info['links']!=1 or info['bytes']>MAX_TEXT or not name.endswith('.md') and name not in moves:continue
        try:
            raw=safe(root,name).read_bytes()
            if not name.endswith('.md'):
                writes[name]={'target':moves[name],'before':identity(root/name),'content':raw};continue
            text=raw.decode('utf-8')
            # Signed/enveloped evidence requires a schema-specific replacement; do not corrupt its digest.
            if 'axis.coordination/' in text or 'SHA-256:' in text or '<!-- axis:sha256' in text or 'checksum-sha256:' in text:
                changed=text
                if rewrite_links(name,text,moves)!=text:residual.append({'path':name,'reason':'sealed historical links retained; compatibility lookup supplies moved record identity'})
            else:
                changed=rewrite_links(name,text,moves)
                path=Path(name)
                if path.parent.as_posix()=='_Axis/Tasks' and valid_id(path.stem) and re.match(r'^# Task: [^\n]+\n',text) and re.search(r'^status: (Active|Blocked|Completed|Cancelled)$',text,re.M) and not re.search(r'^created:',text,re.M):
                    changed=changed.replace('\nstatus:', '\ncreated: '+path.stem+'\nstatus:',1)
                if name=='_Axis/TASKS.md':
                    # The existing index remains intact. Add only a link to a
                    # corroborated active Task omitted from it, without copying
                    # stale status claims or replacing user-authored summaries.
                    for task in sorted(scan['files']):
                        tp=Path(task)
                        if tp.parent.as_posix()!='_Axis/Tasks' or tp.suffix!='.md':continue
                        canonical=moves.get(task,task);tid=Path(canonical).stem
                        if not valid_id(tid) or tid in changed:continue
                        try:detail=safe(root,task).read_text()
                        except (OSError,ValueError,UnicodeError):continue
                        title=re.match(r'^# Task: ([^\n]+)\n',detail)
                        if not title or not re.search(r'^status: (Active|Blocked)$',detail,re.M):continue
                        if any(c in title[1] for c in '[]<>'):continue
                        changed+='\n## '+title[1]+'\n\n[Details...]('+canonical[len('_Axis/'):] +')\n'

            target=moves.get(name,name)
            if changed!=text or target!=name:
                writes[name]={'target':target,'before':identity(root/name),'content':changed.encode()}
        except (OSError,ValueError,UnicodeError):
            if name in moves:
                raise ValueError('dependent repair inputs unavailable')
    # No content map can reference a move whose original was not successfully prepared.
    if set(moves)-set(writes):raise ValueError('incomplete repair preparation')
    guard();journal.mkdir(exist_ok=True)
    operations=[];head=checkpoint(root)
    for index,(name,item) in enumerate(sorted(writes.items())):
        guard();raw=safe(root,name).read_bytes()
        if identity(safe(root,name))!=item['before']:raise ValueError('repair input changed during preparation')
        op={'source':name,'target':item['target'],'before':item['before'],'after':{'sha256':digest(item['content']),'bytes':len(item['content']),'mode':item['before']['mode']},'index':index}
        if item['target']!=name and (root/item['target']).exists():op['target_before']=identity(root/item['target'])
        if head:
            try:
                q=subprocess.run(['git','-C',str(root),'show',head+':'+name],capture_output=True,timeout=10)
                if q.returncode==0 and q.stdout==raw:op['git_before']=head
            except (OSError,subprocess.SubprocessError):pass
        copies=[]
        if not op.get('git_before'):copies.append((journal/(str(index)+'.before'),raw))
        if op['after']!=op['before']:copies.append((journal/(str(index)+'.after'),item['content']))
        for path,data in copies:
            with path.open('xb') as out:out.write(data);out.flush();os.fsync(out.fileno())
        operations.append(op)
    plan={'schema':1,'conventions':CONVENTIONS,'operations':operations,'moves':moves,'residual':scan['residual']+residual,'coverage':scan['counts'],'roots':scan['roots']}
    once(journal/'plan.json',plan);return plan


def apply(root,journal,guard):
    """One dependency-consistent unit. Crash resumes only exact known states."""
    plan=json.loads((journal/'plan.json').read_text())
    if not any(journal.glob('*.done')) and not any(journal.glob('*.pending')):
        for op in plan['operations']:
            if identity(safe(root,op['source']))!=op['before'] or op['source']!=op['target'] and identity(safe(root,op['target']))!=op.get('target_before'):
                result={'schema':1,'coverage':plan['coverage'],'roots':plan['roots'],'repairs':0,'moves':{},'residual':plan['residual']+[{'path':op['source'],'reason':'input changed before repair; left in place'}],'status':'best-effort-complete','outcome':'skipped'}
                once(journal/'result.json',result);return result
    for op in plan['operations']:
        pending=journal/(str(op['index'])+'.pending')
        if pending.exists() and pending.stat().st_nlink==2:
            target=safe(root,op['target'])
            if not target.exists() or not pending.samefile(target) or digest(pending.read_bytes())!=op['after']['sha256']:raise ValueError('unowned pending publication link')
            guard();pending.unlink();syncdir(journal)
        guard();source=safe(root,op['source']);target=safe(root,op['target']);i=op['index']
        before=recovery(root,journal,op,'before');after=recovery(root,journal,op,'after')
        if digest(before)!=op['before']['sha256'] or digest(after)!=op['after']['sha256']:raise ValueError('repair recovery input changed')
        if (journal/(str(i)+'.done')).exists():
            if identity(target)!=op['after'] or source!=target and source.exists():raise ValueError('completed repair changed')
            continue
        if source!=target:
            if identity(target)==op['after']:
                if source.exists():
                    if identity(source)!=op['before']:raise ValueError('third-value source after interrupted move')
                    guard();source.unlink();syncdir(source.parent)
                once(journal/(str(i)+'.done'),{'applied':True});continue
            if identity(source)!=op['before'] or target.exists():raise ValueError('repair conflict; exact originals retained')
        elif identity(source) not in (op['before'],op['after']):raise ValueError('third-value edit; preserve for recovery')
        target.parent.mkdir(parents=True,exist_ok=True);safe(root,op['target']);guard()
        temporary=journal/(str(i)+'.pending')
        if temporary.exists():temporary.unlink()
        with temporary.open('xb') as out:out.write(after);out.flush();os.fsync(out.fileno())
        os.chmod(temporary,op['after']['mode']);guard()
        if source==target:
            if identity(source) not in (op['before'],op['after']):raise ValueError('third-value edit at commit')
            os.replace(temporary,target)
        else:
            # Exclusive link, then remove the exact old source; replay handles the pair.
            os.link(temporary,target);temporary.unlink()
            if identity(source)!=op['before']:raise ValueError('source changed after destination creation')
            source.unlink()
        syncdir(target.parent)
        if source!=target:syncdir(source.parent)
        if identity(target)!=op['after']:raise ValueError('repair readback failed')
        once(journal/(str(i)+'.done'),{'applied':True})
    for source in sorted(plan['moves'],key=lambda n:len(n),reverse=True):
        old_parent=safe(root,source).parent
        while old_parent.relative_to(root).as_posix() not in ROOTS and old_parent.name not in FAMILIES:
            try:
                guard();old_parent.rmdir()
            except OSError:break
            old_parent=old_parent.parent
    result={'schema':1,'coverage':plan['coverage'],'roots':plan['roots'],'repairs':len(plan['operations']),'conventions':CONVENTIONS,'dispositions':[{k:op[k] for k in ('source','target','before','after')} for op in plan['operations']],'moves':plan['moves'],'residual':plan['residual'],'status':'best-effort-complete'}
    if not (journal/'result.json').exists():once(journal/'result.json',result)
    return result


def rollback(root,journal,guard):
    """Restore only exact owned states; an unowned edit is never overwritten."""
    plan=json.loads((journal/'plan.json').read_text())
    for op in reversed(plan['operations']):
        guard();source=safe(root,op['source']);target=safe(root,op['target']);i=op['index']
        before=recovery(root,journal,op,'before')
        if digest(before)!=op['before']['sha256']:raise ValueError('repair recovery preimage changed')
        if source==target:
            current=identity(source)
            if current==op['before']:continue
            if current!=op['after']:raise ValueError('unowned edit during optional repair recovery')
            tmp=journal/(str(i)+'.restore')
            with tmp.open('wb') as out:out.write(before);out.flush();os.fsync(out.fileno())
            os.chmod(tmp,op['before']['mode']);guard();os.replace(tmp,source)
        else:
            a,b=identity(source),identity(target)
            if a not in (None,op['before']) or b not in (None,op['after']):raise ValueError('unowned move state during optional repair recovery')
            if a is None:
                source.parent.mkdir(parents=True,exist_ok=True)
                with source.open('xb') as out:out.write(before);out.flush();os.fsync(out.fileno())
                os.chmod(source,op['before']['mode'])
            if b is not None and not op.get('target_before'):guard();target.unlink();syncdir(target.parent)
        syncdir(source.parent)
        if identity(source)!=op['before']:raise ValueError('repair restoration readback failed')
    return True


def run(root,journal,guard,exclude=()):
    root=Path(root);journal=Path(journal)
    if (journal/'result.json').exists():return json.loads((journal/'result.json').read_text())
    if not (journal/'plan.json').exists():
        try:scan=inventory(root,journal,guard)
        except (OSError,ValueError,UnicodeError):scan={'roots':[], 'files':{}, 'directories':[], 'counts':{'files':0,'directories':0,'boundaries':0,'unreadable':1}, 'residual':[{'path':'','reason':'optional inventory unavailable; original content retained'}]}
        # Installed machinery and already-owned semantic reconciliation cannot be
        # rewritten behind the adoption engine's target identity checks.
        scan['excluded']=list(exclude)
        try:prepare(root,scan,journal,guard)
        except Exception as exc:
            guard()
            journal.mkdir(exist_ok=True)
            result={'schema':1,'coverage':scan['counts'],'roots':scan['roots'],'repairs':0,'moves':{},'residual':scan['residual']+[{'path':'','reason':'optional repair preparation unavailable; original content retained ('+type(exc).__name__+')'}],'status':'best-effort-complete','outcome':'skipped'}
            once(journal/'result.json',result);return result
    try:
        result=apply(root,journal,guard)
        return result
    except Exception as exc:
        guard()
        rollback(root,journal,guard)
        plan=json.loads((journal/'plan.json').read_text())
        result={'schema':1,'coverage':plan['coverage'],'roots':plan['roots'],'repairs':0,'moves':{},'residual':plan['residual']+[{'path':'','reason':'optional repair restored; original content retained ('+type(exc).__name__+')'}],'status':'best-effort-complete','outcome':'restored'}
        if not (journal/'result.json').exists():once(journal/'result.json',result)
        return result
