#!/usr/bin/env python3
"""Optional local startup records and record creation. Python3/POSIX only; no network or model calls.

The Agent owns eligibility, instruction loading, update permission and presentation.
This helper owns only the documented mechanical record operations on one root.
Any Index-Detail record, under the caller's own live Marker (body on stdin or --body-file):
  python3 _Axis/Resources/startup-state.py --root . record --session {Session ID} --family Logs
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time
import unicodedata
try:
    import fcntl
except ImportError:
    fcntl = None

ID = re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z')
FAMILIES = ('Agents','Audit','CX','Followups','Ideas','Logs','Notes','Reminders','Reviews','Snapshots','Status','Supervision','Tasks','Teams','Messages','Jobs','Schedules','ColdStorage')
# Reviews/ arrives with the first ^review on projects updated from 2.00; Status/ is the pre-2.01 name it replaces.
OPTIONAL_FAMILIES = ('Reviews','Status','Teams','Messages','Jobs','Schedules','ColdStorage')
CAPS = ('model','host-spawn','host-parallel','host-shell','host-local-llm','host-cloud-sync','host-storage')
OWNER_KEYS = {'schema','kind','token','session','host','phase','starting_log','started_log'}

def replace_shared(src, dst):
    """os.replace with a bounded retry. On shared network folders (SMB) a rename can fail briefly with EBUSY or
    EACCES while another computer reads the target (SMB lab, 2026-10-04: worst wait 1.05 s)."""
    import errno as _errno, time as _time
    deadline=_time.monotonic()+10
    while True:
        try:os.replace(src,dst);return
        except OSError as e:
            if e.errno not in (_errno.EBUSY,_errno.EACCES) or _time.monotonic()>deadline:raise
            _time.sleep(0.05)

class Fault(Exception):
    def __init__(self, code, path=''):
        self.code, self.path = code, path
        super().__init__(code)

def need(condition, code, path=''):
    if not condition:
        raise Fault(code, path)

def parse_stamp(value):
    need(isinstance(value,str) and ID.fullmatch(value), 'timestamp')
    try:
        return dt.datetime.strptime(value,'%Y.%m.%d.%H.%M.%S.%fZ').replace(tzinfo=dt.timezone.utc)
    except ValueError:
        raise Fault('timestamp') from None

def stamp(value=None):
    value = value or dt.datetime.now(dt.timezone.utc)
    return value.strftime('%Y.%m.%d.%H.%M.%S.')+f'{value.microsecond//1000:03d}Z'

def advance(value):
    return stamp(parse_stamp(value)+dt.timedelta(milliseconds=1))

def encoded(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()

def regular(info, name):
    need(stat.S_ISREG(info.st_mode) and info.st_nlink==1, 'unsafe_path', name)

def identity(info):
    return info.st_dev, info.st_ino

def read_fd(fd, name, limit=65536):
    regular(os.fstat(fd),name)
    os.lseek(fd,0,os.SEEK_SET)
    chunks=[];size=0
    while True:
        chunk=os.read(fd,4096)
        if not chunk:break
        chunks.append(chunk);size+=len(chunk)
        need(size<=limit,'record_too_large',name)
    return b''.join(chunks)

def write_fd(fd, data):
    offset=0
    while offset<len(data):
        count=os.write(fd,data[offset:])
        need(count>0,'write_failed')
        offset+=count
    os.fsync(fd)

def archive_root(startup):
    """Resolve [Settings > Archive Location] read-only: (project-relative root, None), (None, absolute or home-relative root), or (None, None) when unavailable."""
    try:value=startup.setting('Archive Location')
    except Fault as error:
        if error.code!='missing_path' or error.path!='_Axis/SETTINGS.md':raise
        value=None
    value=(value or '_Axis/Archive/').strip()
    if value.rstrip('/')=='_Axis/Archive':return '_Axis/Archive',None
    if value.startswith('~/'):
        home=os.path.expanduser('~')
        if not home.startswith('/') or home=='/':return None,None
        value=home.rstrip('/')+value[1:]
    if '\\' in value or '..' in value.split('/'):return None,None
    if value.startswith('/'):
        folder=Path(value.rstrip('/') or '/')
        try:info=os.stat(folder)
        except OSError:return None,None
        return (None,folder) if stat.S_ISDIR(info.st_mode) else (None,None)
    relative=value.rstrip('/')
    try:folder=startup.path(relative,missing=True,kind='directory')
    except Fault:return None,None
    return (relative if folder.exists() else None),None

class Startup:
    def __init__(self, root):
        need('..' not in Path(root).parts,'unsafe_path','root')
        self.root=Path(os.path.abspath(root))
        current=Path(self.root.anchor)
        for part in self.root.parts[1:]:
            current=current/part;info=current.lstat()
            need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode),'unsafe_path','root')
        self.owner_fd=None;self.state=None;self.claim_identity=None
        self.claim_name='_Axis/Flags/starting.lock';self.owner_name=self.claim_name+'/OWNER'
        self.path('_Axis/Flags',kind='directory');self.path('_Axis/Agents',kind='directory');self.path('_Temp',kind='directory')

    def path(self, name, missing=False, kind='file'):
        need(isinstance(name,str) and name and not name.startswith('/') and '\\' not in name and all(p not in ('','.','..') for p in name.split('/')),'unsafe_path',name)
        current=self.root
        parts=name.split('/')
        for i,part in enumerate(parts):
            current=current/part
            try:info=current.lstat()
            except FileNotFoundError:
                if missing and i==len(parts)-1:return current
                raise Fault('missing_path',name) from None
            need(not stat.S_ISLNK(info.st_mode),'unsafe_path',name)
            if i<len(parts)-1 or kind=='directory':need(stat.S_ISDIR(info.st_mode),'unsafe_path',name)
            else:regular(info,name)
        return current

    def read(self, name, optional=False, limit=65536):
        path=self.path(name,missing=optional)
        try:fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
        except FileNotFoundError:
            if optional:return None
            raise Fault('missing_path',name) from None
        try:return read_fd(fd,name,limit).decode('utf-8')
        finally:os.close(fd)

    def exists(self, name):
        try:self.path(name);return True
        except Fault as error:
            if error.code=='missing_path':return False
            raise

    def merge_access(self):
        # Source-side maintenance retires all writing authority, including a previously booted session.
        # Destination Main retains only the recovery lane under the Merging practice.
        need(not self.exists('_Axis/Merges/retired.json'),'merge_retired','_Axis/Merges/retired.json')
        raw=self.read('_Axis/Flags/merge-pending',optional=True,limit=4096)
        if raw is None:return
        try:value=json.loads(raw)
        except (ValueError,TypeError):raise Fault('merge_state_invalid','_Axis/Flags/merge-pending') from None
        need(isinstance(value,dict) and set(value)=={'schema','transaction','plan_sha256','destination_id','source_id'} and value.get('schema')==1 and re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z',str(value.get('transaction',''))) and re.fullmatch(r'[0-9a-f]{64}',str(value.get('plan_sha256',''))),'merge_state_invalid','_Axis/Flags/merge-pending')
        project=self.read('_Axis/PROJECT.md');ids=re.findall(r'^project-id: (\S+)\s*$',project,re.M)
        need(len(ids)==1 and isinstance(value.get('destination_id'),str) and isinstance(value.get('source_id'),str) and value['destination_id']!=value['source_id'] and ids[0] in (value['source_id'],value['destination_id']),'merge_state_invalid','_Axis/Flags/merge-pending')
        need(ids[0]==value['destination_id'],'merge_source_held','_Axis/Flags/merge-pending')

    def owner_check(self):
        need(self.owner_fd is not None and self.state is not None,'owner_missing',self.owner_name)
        directory=self.path(self.claim_name,kind='directory')
        need(identity(directory.stat())==self.claim_identity,'owner_changed',self.claim_name)
        path=self.path(self.owner_name)
        need(identity(path.stat())==identity(os.fstat(self.owner_fd)),'owner_changed',self.owner_name)
        need(read_fd(self.owner_fd,self.owner_name)==encoded(self.state),'owner_changed',self.owner_name)

    def owner_update(self, **changes):
        self.owner_check()
        new=dict(self.state,**changes)
        os.lseek(self.owner_fd,0,os.SEEK_SET);os.ftruncate(self.owner_fd,0)
        write_fd(self.owner_fd,encoded(new))
        need(read_fd(self.owner_fd,self.owner_name)==encoded(new),'owner_readback',self.owner_name)
        self.state=new;self.owner_check()

    @property
    def sid(self):return self.state['session']
    @property
    def marker_name(self):return '_Axis/Agents/'+self.sid+'.md'
    def marker_body(self):return f'Main: session\n\nsession: {self.sid}\nhost: {self.state["host"]}\n'

    def foreign_mains(self):
        found=[];now=time.time()
        for path in sorted(self.path('_Axis/Agents',kind='directory').glob('*.md')):
            if self.state and self.state['phase']!='claiming' and path.name==self.sid+'.md':continue
            name=path.relative_to(self.root).as_posix();text=self.read(name)
            if text.splitlines()[:1]!=['Main: session']:continue
            if self.exists(name[:-3]+'.kill'):continue
            age=now-path.stat().st_mtime
            if age>=3600:continue
            lines=text.splitlines()
            need(len(lines)==4 and lines[1]=='' and lines[2]=='session: '+path.stem and lines[3].startswith('host: ') and lines[3][6:].strip(),'marker_invalid',name)
            parse_stamp(path.stem)
            found.append({'session':path.stem,'host':lines[3][6:],'age_seconds':age})
        return found

    def last_activity(self, sid, mtime):
        """Newest sign of a Main session: Marker mtime, its last Tracking line, or a newer Log naming it."""
        best=mtime
        def when(text):
            try:return parse_stamp(text).timestamp()
            except Fault:return None
        tracking=''
        try:
            path=self.path('_Axis/Tracking/'+sid+'.md',missing=True)
            if path.exists():
                fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
                try:
                    regular(os.fstat(fd),path.name);os.lseek(fd,max(0,os.fstat(fd).st_size-16384),os.SEEK_SET)
                    tracking=os.read(fd,16384).decode('utf-8','replace')
                finally:os.close(fd)
        except (Fault,OSError):pass
        for line in tracking.splitlines()[-50:]:
            value=when(line.split(' - ',1)[0].strip())
            if value is not None and value>best:best=value
        try:names=sorted((p.name for p in self.path('_Axis/Logs',kind='directory').glob('*Z.md')),reverse=True)
        except (Fault,OSError):names=[]
        for name in names[:2000]:
            value=when(name[:-3])
            if value is None:continue
            if value<=best:break
            try:text=self.read('_Axis/Logs/'+name)
            except (Fault,OSError,UnicodeError):continue
            if 'session: '+sid in text.splitlines()[:12]:best=value;break
        return best

    def idle_mains(self):
        """Foreign Main Markers at or over 1 hour old, without tombstone, with their measured idle time."""
        found=[];now=time.time()
        for path in sorted(self.path('_Axis/Agents',kind='directory').glob('*Z.md')):
            name=path.relative_to(self.root).as_posix()
            try:
                text=self.read(name);mtime=path.stat().st_mtime
                if text.splitlines()[:1]!=['Main: session'] or self.exists(name[:-3]+'.kill') or now-mtime<3600:continue
            except (Fault,OSError,UnicodeError):continue
            lines=text.splitlines();host=lines[3][6:] if len(lines)>3 and lines[3].startswith('host: ') else ''
            found.append({'session':path.stem,'host':host,'idle_seconds':int(now-self.last_activity(path.stem,mtime))})
        return found

    def permissions(self):
        try:value=self.setting('Permissions')
        except Fault as error:
            if error.code!='missing_path':raise
            value=None
        return value if value in ('Restricted','Default','Autonomous') else 'Default'

    def sweep(self, retire, explicit=()):
        """After admission: delete retired Main Markers, other Markers over 24 hours old and tombstones over 1 hour old."""
        self.guard();now=time.time();cleared=0
        def remove(name, minimum):
            nonlocal cleared
            try:
                path=self.path(name)
                before=path.stat()
                if now-before.st_mtime<minimum:return
                raw=self.read(name);intent=None
                if raw.startswith('Main: session\n'):
                    old_host=next((line[6:] for line in raw.splitlines() if line.startswith('host: ')),'unverified')
                    idle=int(max(0,now-self.last_activity(path.stem,path.stat().st_mtime)))
                    basis='explicit User takeover' if path.stem in explicit else 'applicable Permissions takeover threshold or stale lifecycle sweep'
                    detail=f'displaced-session: {path.stem}\nhost: {old_host}\nidle-seconds: {idle}\nauthorization: {basis}\n'
                    intent,_=self.record('Logs',lambda _:f'Main displacement prepared\n\nby: Main Agent\nsession: {self.sid}\n'+detail+'Removal intent only; completion must be verified separately.\n')
                    self.guard();need(self.read(name)==raw,'marker_changed',name)
                current=path.stat()
                need(identity(current)==identity(before) and current.st_mtime_ns==before.st_mtime_ns,'marker_changed',name)
                os.unlink(path);cleared+=1
                if intent:
                    need(not path.exists(),'marker_removal_unverified',name)
                    self.record('Logs',lambda _:f'Main displaced\n\nby: Main Agent\nsession: {self.sid}\n'+detail+f'prepared: {intent}\nVerified old Marker absent after removal. Persistent host conversation may still be open.\n')
            except FileNotFoundError:pass
            except (Fault,OSError):pass
        for path in sorted(self.path('_Axis/Agents',kind='directory').glob('*Z.kill')):
            if now-path.stat().st_mtime>3600 and path.stem!=self.sid:remove('_Axis/Agents/'+path.stem+'.md',0);remove('_Axis/Agents/'+path.name,3600)
        for path in sorted(self.path('_Axis/Agents',kind='directory').glob('*Z.md')):
            if path.stem==self.sid:continue
            remove('_Axis/Agents/'+path.name,3600 if path.stem in retire else 86400)
        self.guard()
        return cleared

    def guard(self, starting=True, foreign=True):
        self.merge_access()
        self.owner_check()
        if self.exists('_Axis/Agents/'+self.sid+'.kill'):raise Fault('lease_killed',self.marker_name)
        text=self.read(self.marker_name,optional=True)
        need(text is not None,'lease_missing',self.marker_name)
        need(text==self.marker_body(),'marker_mismatch',self.marker_name)
        if foreign:need(not self.foreign_mains(),'foreign_main','_Axis/Agents')
        if starting:
            value=self.read('_Axis/Flags/starting',optional=True)
            need(value is not None,'starting_missing','_Axis/Flags/starting')
            need(value.splitlines()[:1]==[self.sid],'starting_mismatch','_Axis/Flags/starting')

    def renew(self, name, expected):
        self.guard()
        path=self.path(name);fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            need(read_fd(fd,name)==expected.encode(),'readback',name)
            self.guard()
            need(identity(path.stat())==identity(os.fstat(fd)),'path_changed',name)
            regular(os.fstat(fd),name)
            os.utime(fd,None)
            need(identity(self.path(name).stat())==identity(os.fstat(fd)),'path_changed',name)
            self.guard()
        finally:os.close(fd)

    def write_flag(self, name, text, bootstrap=False):
        if bootstrap:self.owner_check()
        else:self.guard()
        relative='_Axis/Flags/'+name;destination=self.path(relative,missing=True)
        temporary=relative+'.'+secrets.token_hex(12)+'.tmp';path=self.path(temporary,missing=True)
        fd=os.open(path,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
        try:write_fd(fd,text.encode());need(read_fd(fd,temporary)==text.encode(),'readback',temporary)
        finally:os.close(fd)
        if bootstrap:self.owner_check()
        else:self.guard()
        self.path(relative,missing=True)
        replace_shared(path,destination)
        need(self.read(relative)==text,'readback',relative)

    def clear_flag(self, name, starting=True):
        self.guard(starting=starting)
        relative='_Axis/Flags/'+name;path=self.path(relative,missing=True)
        try:os.unlink(path)
        except FileNotFoundError:return
        except PermissionError:
            self.write_flag(name,'cleared\n'+stamp()+'\n')
        value=self.read(relative,optional=True)
        need(value is None or value.splitlines()[:1]==['cleared'],'clear_failed',relative)

    def release_admission(self, lease=False):
        if lease:self.guard(starting=False)
        else:self.owner_check()
        os.unlink(self.path(self.owner_name))
        # Close the unlinked OWNER before rmdir: on SMB shares a deleted file stays "delete pending" while open, so
        # rmdir fails ENOTEMPTY (Phase 2 on Apple SMB, 2026-10-04). The claim directory still blocks new admission.
        if self.owner_fd is not None:os.close(self.owner_fd);self.owner_fd=None
        os.rmdir(self.path(self.claim_name,kind='directory'))
        need(not (self.root/self.claim_name).exists(),'release_failed',self.claim_name)

    def collision(self, candidate):
        occupied=False;roots=[]
        for relative in ['_Axis/'+family for family in FAMILIES]+['_Axis/Archive']:
            if relative[6:] in OPTIONAL_FAMILIES and not os.path.lexists(self.root/relative):continue
            roots.append((self.path(relative,kind='directory'),relative))
        relative,external=archive_root(self)
        archive=self.path(relative,kind='directory') if relative else external
        if archive is not None and archive not in [item[0] for item in roots]:
            current=Path(archive.anchor)
            for part in archive.parts[1:]:
                current/=part;info=current.lstat()
                need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode),'unsafe_path','Archive')
            roots.append((archive,'_Axis/Archive'))
        if os.path.lexists(self.root/'_Memos'):
            roots.append((self.path('_Memos',kind='directory'),'_Memos'))
        for base,label in roots:
            stack=[base]
            while stack:
                parent=stack.pop()
                with os.scandir(parent) as entries:
                    for entry in entries:
                        info=entry.stat(follow_symlinks=False);name=label+'/'+Path(entry.path).relative_to(base).as_posix()
                        need(not stat.S_ISLNK(info.st_mode),'unsafe_path',name)
                        if stat.S_ISDIR(info.st_mode):stack.append(Path(entry.path))
                        else:
                            regular(info,name)
                            if entry.name==candidate+'.md' or (label=='_Memos' and entry.name.startswith(candidate+' - ') and entry.name.endswith('.md')):occupied=True
        # Admission reserves cold IDs as data; it never loads another executable.
        cold='_Axis/ColdStorage'
        if os.path.lexists(self.root/cold):
            for path in self.path(cold,kind='directory').glob('*.md'):
                name=cold+'/'+path.name;parse_stamp(path.stem)
                text=self.read(name,limit=131072)
                blocks=re.findall(r'```axis-cold-storage\n(.*?)\n```',text,re.S)
                need(len(blocks)==1,'cold_catalog',name)
                value=json.loads(blocks[0]);need(value.get('schema')==1 and value.get('id')==path.stem and isinstance(value.get('files'),list),'cold_catalog',name)
                for item in value['files']:
                    need(isinstance(item,dict) and 'record_id' in item,'cold_catalog',name)
                    ident=item['record_id']
                    if ident is not None:parse_stamp(ident);occupied=occupied or ident==candidate
        return occupied

    def release_timestamp(self, relative, body, expected_identity, deadline):
        need(time.monotonic()-deadline<10,'claim_expired',relative)
        need(identity(self.path(relative,kind='directory').stat())==expected_identity,'timestamp_owner',relative)
        need(self.read(relative+'/OWNER')==body,'timestamp_owner',relative)
        os.unlink(self.path(relative+'/OWNER'));os.rmdir(self.path(relative,kind='directory'))

    def record(self, family, body, initial=None, bootstrap=False, renew_lease=True, memo_subject=None, message_directory=None):
        need(type(renew_lease) is bool,'renew_lease')
        if message_directory is not None:
            need(family=='Messages' and (message_directory=='_Axis/Messages/Individual' or re.fullmatch(r'_Axis/Messages/Teams/\d{4}(?:\.\d{2}){5}\.\d{3}Z',message_directory)), 'message_directory')
            self.path(message_directory,kind='directory')
        candidate=initial or stamp();parse_stamp(candidate)
        for _ in range(1000):
            content=body(candidate)
            raw=content.encode();record_limit=131072 if family in ('Teams','Messages','Jobs','Schedules','ColdStorage') else 65536
            need(len(raw)<=record_limit,'record_too_large',family)
            if bootstrap:self.owner_check()
            else:self.guard()
            relative='_Temp/'+candidate+'.tsclaim';path=self.path(relative,missing=True,kind='directory');started=time.monotonic()
            try:os.mkdir(path)
            except FileExistsError:candidate=advance(candidate);continue
            claim_identity=identity(path.stat());owner=secrets.token_hex(16)+'\n'+(candidate if bootstrap else self.sid)+'\n'
            owner_path=self.path(relative+'/OWNER',missing=True);fd=os.open(owner_path,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
            try:write_fd(fd,owner.encode());need(read_fd(fd,relative+'/OWNER')==owner.encode(),'timestamp_owner',relative)
            finally:os.close(fd)
            occupied=self.collision(candidate)
            need(time.monotonic()-started<10,'claim_expired',relative)
            if occupied:
                self.release_timestamp(relative,owner,claim_identity,started);candidate=advance(candidate);continue
            if bootstrap:
                need(not self.exists('_Axis/Agents/'+candidate+'.kill'),'lease_killed','_Axis/Agents/'+candidate+'.md');self.owner_check()
            else:self.guard()
            need(self.read(relative+'/OWNER')==owner,'timestamp_owner',relative)
            name=('_Memos/'+candidate+' - '+memo_subject+'.md') if memo_subject is not None else ((message_directory or '_Axis/'+family)+'/'+candidate+'.md');destination=self.path(name,missing=True)
            need(time.monotonic()-started<10,'claim_expired',relative)
            fd=os.open(destination,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
            try:write_fd(fd,raw);need(read_fd(fd,name,record_limit)==raw,'record_readback',name)
            finally:os.close(fd)
            need(self.read(name,limit=record_limit)==content,'record_readback',name)
            if bootstrap:need(not self.exists('_Axis/Agents/'+candidate+'.kill'),'lease_killed',name)
            else:self.guard()
            self.release_timestamp(relative,owner,claim_identity,started)
            if not bootstrap and renew_lease:self.renew(self.marker_name,self.marker_body())
            return candidate,name
        raise Fault('collision_limit')

    def claim(self, initial, host, take_over=()):
        self.merge_access()
        parse_stamp(initial)
        need(parse_stamp(initial)<=dt.datetime.now(dt.timezone.utc),'timestamp_future')
        need(isinstance(host,str) and host.strip()==host and 0<len(host)<=120 and all(ord(c)>=32 for c in host),'host')
        path=self.path(self.claim_name,missing=True,kind='directory')
        try:os.mkdir(path)
        except FileExistsError:raise Fault('occupied_admission',self.claim_name) from None
        self.claim_identity=identity(path.stat());token=secrets.token_hex(16)
        self.owner_fd=os.open(self.path(self.owner_name,missing=True),os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
        fcntl.flock(self.owner_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.state={'schema':1,'kind':'axis-startup-admission','token':token,'session':initial,'host':host,'phase':'claiming','starting_log':None,'started_log':None}
        write_fd(self.owner_fd,encoded(self.state));self.owner_check()
        try:self.merge_access()
        except Fault:
            self.release_admission();raise
        prior=self.read('_Axis/Flags/starting',optional=True)
        if prior is not None and prior.splitlines() and prior.splitlines()[0].strip() not in ('','cleared'):
            self.release_admission();raise Fault('unfinished_starting','_Axis/Flags/starting')
        foreign=self.foreign_mains()
        if foreign:self.release_admission();return {'status':'external','mains':foreign}
        # Takeover of an idle Main (Claim-Session > Takeover): active within 1 hour joins as External; under the
        # Permissions threshold asks User; at or over it, or named by User's --take-over, is retired after admission.
        idle=self.idle_mains();recent=[m for m in idle if m['idle_seconds']<3600]
        if recent:self.release_admission();return {'status':'external','mains':recent}
        level=self.permissions() if idle else 'Default';limit={'Restricted':24,'Default':7,'Autonomous':3}[level]
        ask=[m for m in idle if m['idle_seconds']<limit*3600 and m['session'] not in take_over]
        if ask:self.release_admission();return {'status':'ask','mains':ask,'permissions':level,'threshold_hours':limit}
        final,name=self.record('Agents',lambda value:f'Main: session\n\nsession: {value}\nhost: {host}\n',initial,bootstrap=True)
        self.owner_update(session=final,phase='admitted')
        self.write_flag('starting',final+'\n'+stamp()+'\n',bootstrap=True)
        self.guard()
        cleared=self.sweep({m['session'] for m in idle},take_over)
        return {'status':'admitted','session':final,'owner':token,'marker':name,'took_over':idle,'cleared':cleared,'permissions':level,'threshold_hours':limit}

    def load(self, session, token, readonly=False):
        parse_stamp(session);need(re.fullmatch('[0-9a-f]{32}',token),'owner_mismatch',self.owner_name)
        directory=self.path(self.claim_name,kind='directory');self.claim_identity=identity(directory.stat())
        self.owner_fd=os.open(self.path(self.owner_name),(os.O_RDONLY if readonly else os.O_RDWR)|os.O_NOFOLLOW)
        regular(os.fstat(self.owner_fd),self.owner_name)
        try:fcntl.flock(self.owner_fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        # flock contention reads as EACCES on macOS SMB mounts (SMB lab, 2026-10-04), EWOULDBLOCK elsewhere.
        except (BlockingIOError,PermissionError):raise Fault('operation_busy',self.owner_name) from None
        try:value=json.loads(read_fd(self.owner_fd,self.owner_name))
        except (ValueError,UnicodeError):raise Fault('owner_malformed',self.owner_name) from None
        need(isinstance(value,dict) and set(value)==OWNER_KEYS and value['schema']==1 and value['kind']=='axis-startup-admission','owner_malformed',self.owner_name)
        need(value['session']==session and value['token']==token,'owner_mismatch',self.owner_name)
        need(value['phase'] in ('claiming','admitted','initialized','committing') and isinstance(value['host'],str) and value['host'] and '\n' not in value['host'],'owner_malformed',self.owner_name)
        self.state=value;self.owner_check()

    def check_indexes(self):
        """Inspect only Task/Snapshot links and filenames; never open detail bodies."""
        need(self.state['phase']=='initialized','phase',self.owner_name)
        self.guard()
        deadline=time.monotonic()+5
        inside,outside=archive_root(self)
        if inside is None and outside is None:return {'status':'unavailable','reason':'archive_location_unavailable'}
        def metadata(path):
            value=path.lstat()
            return (value.st_dev,value.st_ino,value.st_mode,value.st_nlink,value.st_size,value.st_mtime_ns,value.st_ctime_ns)
        def capture():
            result={}
            for family,index in (('Tasks','TASKS.md'),('Snapshots','SNAPSHOTS.md')):
                name='_Axis/'+index;path=self.path(name)
                fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
                try:
                    before=metadata(path)
                    need(identity(path.stat())==identity(os.fstat(fd)),'path_changed',name)
                    text=read_fd(fd,name,262144).decode('utf-8')
                    need(metadata(path)==before,'index_changed',name)
                finally:os.close(fd)
                files={};directories={}
                for relative in (family,family+'/Archive','Archive/'+family):
                    directory='_Axis/'+relative
                    if relative.startswith('Archive/') and outside is not None:
                        directory=str(outside/family);folder=outside/family
                        if folder.is_symlink() or not folder.is_dir():continue
                    elif relative.startswith('Archive/'):
                        archive=self.path(inside,missing=True,kind='directory')
                        if not archive.exists():continue
                        directory=inside+'/'+family
                        folder=self.path(directory,missing=True,kind='directory')
                    else:folder=self.path(directory,missing=True,kind='directory')
                    if not folder.exists():continue
                    directories[relative]=metadata(folder)
                    with os.scandir(folder) as listing:
                        for entry in listing:
                            need(time.monotonic()<deadline,'inspection_limit')
                            need(len(files)<10000,'inspection_limit',directory)
                            item=relative+'/'+entry.name;info=entry.stat(follow_symlinks=False)
                            if relative==family and entry.name=='Archive' and stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode):continue
                            if relative.endswith('/Archive') and entry.name=='COLD.md' and stat.S_ISREG(info.st_mode):continue
                            regular(info,directory+'/'+entry.name)
                            if entry.name=='.gitkeep':continue
                            need(entry.name.endswith('.md') and ID.fullmatch(entry.name[:-3]),'unexpected_entry',directory+'/'+entry.name)
                            parse_stamp(entry.name[:-3])
                            files[item]=metadata(Path(entry.path))
                    need(directories[relative]==metadata(folder),'index_changed',directory)
                result[family]=(text,before,files,directories)
            return result
        before=capture();issues=[];issue_count=0;counts={};identities={}
        def issue(family,code,path):
            nonlocal issue_count
            issue_count+=1
            if len(issues)<32:issues.append({'family':family,'code':code,'path':path})
        for family,(text,_,files,_) in before.items():
            links=[]
            for number,section in enumerate(re.split(r'(?m)^##[ \t]+',text)[1:],1):
                if '{{' in section:continue
                matches=re.findall(r'\[Details\.\.\.\]\(([^)\n]*)\)',section)
                if len(matches)!=1 or section.count('[Details...]')!=1:
                    issue(family,'entry_link_count','entry '+str(number))
                for link in matches:
                    found=re.fullmatch(r'(?:Archive/)?'+family+r'/(?:Archive/)?('+ID.pattern+r')\.md',link)
                    if found:
                        try:parse_stamp(found[1])
                        except Fault:found=None
                    if not found:issue(family,'invalid_link','entry '+str(number));continue
                    links.append(link)
            counts[family]={'entries':len(links),'files':len(files)}
            linked={}
            for link in links:linked[link]=linked.get(link,0)+1
            for link,count in linked.items():
                if count!=1:issue(family,'duplicate_link',link)
                if link not in files:issue(family,'missing_detail',link)
            for name in files:
                if name not in linked and not name.startswith((family+'/Archive/','Archive/'+family+'/')):issue(family,'unindexed_detail',name)
                record=name.rsplit('/',1)[-1]
                if record in identities:issue(family,'duplicate_identity',name)
                identities[record]=name
        self.guard()
        need(capture()==before,'index_changed')
        self.guard()
        return {'status':'indexes-checked','outcome':'mismatch' if issue_count else 'clear','counts':counts,'issue_count':issue_count,'issues':issues,'issues_truncated':issue_count>len(issues)}

    def setting(self, name):
        text=self.read('_Axis/SETTINGS.md');sections=re.findall(r'^### '+re.escape(name)+r'\s*\n(.*?)(?=^### |\Z)',text,re.M|re.S)
        need(len(sections)<=1,'setting_ambiguous','_Axis/SETTINGS.md')
        if not sections:return None
        values=re.findall(r'^\*\*Value:\*\* ([^\n]*)$',sections[0],re.M)
        need(len(values)<=1,'setting_ambiguous','_Axis/SETTINGS.md')
        return values[0].strip() if values else None

    def tracking(self, require_opening):
        if self.setting('Tracking')=='off':return None
        name='_Axis/Tracking/'+self.sid+'.md';text=self.read(name,optional=True)
        opening=False
        for line in (text or '').splitlines():
            if not line.strip():continue
            parts=line.split(' - ',2)
            need(len(parts)==3 and parts[1]==self.sid and parts[2].strip(),'tracking_malformed',name);parse_stamp(parts[0])
            opening |= parts[2]=='Session start'
        if require_opening:need(opening,'tracking_opening',name)
        return name,text or '',opening

    def initialize(self):
        need(self.state['phase']=='admitted','phase',self.owner_name);self.guard()
        inside,_=archive_root(self)
        if inside=='_Axis/Archive':
            archive=self.path('_Axis/Archive/Messages',missing=True,kind='directory')
            if not archive.exists():
                self.guard();archive.mkdir();self.path('_Axis/Archive/Messages',kind='directory')
        self.renew('_Axis/Flags/starting',self.read('_Axis/Flags/starting'))
        tracking=self.tracking(False)
        if tracking is not None:
            name,old,opening=tracking;need(not opening,'already_initialized',name);self.guard()
            line=stamp()+' - '+self.sid+' - Session start\n'
            changelog=self.read('_Axis/CHANGELOG.md',optional=True,limit=4194304) or ''
            versions=re.findall(r'^current-version: (\S+)$',changelog,re.M)
            if len(versions)==1:line+=stamp()+' - '+self.sid+' - STATUS [session] Axis boot version: '+versions[0]+'\n'
            fd=os.open(self.path(name,missing=True),os.O_WRONLY|os.O_APPEND|os.O_CREAT|os.O_NOFOLLOW,0o644)
            try:regular(os.fstat(fd),name);write_fd(fd,line.encode())
            finally:os.close(fd)
            need(self.read(name)==old+line,'tracking_readback',name)
        _,log=self.record('Logs',lambda _:f'Session Starting\n\nby: Main Agent\nsession: {self.sid}\n')
        self.owner_update(phase='initialized',starting_log=log)
        return {'status':'initialized','session':self.sid,'starting_log':log}

    def record_capabilities(self, observations):
        need(self.state['phase']=='initialized','phase',self.owner_name);self.guard()
        need(isinstance(observations,str) and len(observations)<=8192,'observations')
        def unique(pairs):
            values={}
            for key,value in pairs:
                need(key not in values,'observations');values[key]=value
            return values
        try:values=json.loads(observations,object_pairs_hook=unique)
        except (ValueError,RecursionError):raise Fault('observations') from None
        need(isinstance(values,dict) and set(values)==set(CAPS),'observations')
        for name in CAPS:
            value=values[name]
            need(isinstance(value,str) and 0<len(value)<=512 and all(ord(c)>=32 and ord(c)!=127 for c in value),'observations',name)
            need(len(value.splitlines())==1,'observations',name)
            value.encode('utf-8') # Reject unencodable data before creating any flag temporary.
            if name=='model':valid=bool(value.strip()) and value!='cleared'
            elif name=='host-storage':valid=value in ('atomic','serialized','unknown')
            else:valid=value in ('yes','no')
            need(valid,'capability_domain',name)
        policy=self.setting('Storage Policy')
        need((policy=='auto' or values['host-storage']=='serialized') and not (values['host-storage']=='atomic' and values['host-cloud-sync']=='yes'),'storage_ceiling')
        when=stamp();need(parse_stamp(self.sid)<=parse_stamp(when),'capability_time')
        # Preflight every destination before any write; later failures retain partial evidence.
        for name in CAPS:self.path('_Axis/Flags/'+name,missing=True)
        self.guard()
        for name in CAPS:
            body=values[name]+'\n'+when+'\n'
            if name=='host-local-llm' and values[name]=='yes':body+='http://localhost:11434/v1\n'
            self.write_flag(name,body)
        self.validate_capabilities();self.guard()
        return {'status':'capabilities-recorded','session':self.sid}

    def validate_capabilities(self):
        now=dt.datetime.now(dt.timezone.utc);values={}
        for name in CAPS:
            text=self.read('_Axis/Flags/'+name);lines=text.splitlines();need(len(lines)>=2,'capability_shape','_Axis/Flags/'+name)
            value=lines[0];when=parse_stamp(lines[1]);need(parse_stamp(self.sid)<=when<=now,'capability_time','_Axis/Flags/'+name)
            if name=='model':valid=bool(value.strip()) and value!='cleared'
            elif name=='host-storage':valid=value in ('atomic','serialized','unknown')
            else:valid=value in ('yes','no')
            need(valid,'capability_domain','_Axis/Flags/'+name)
            if name=='host-local-llm' and value=='yes':need(len(lines)==3 and lines[2]=='http://localhost:11434/v1','capability_shape','_Axis/Flags/'+name)
            else:need(len(lines)==2,'capability_shape','_Axis/Flags/'+name)
            values[name]=value
        policy=self.setting('Storage Policy')
        need((policy=='auto' or values['host-storage']=='serialized') and not (values['host-storage']=='atomic' and values['host-cloud-sync']=='yes'),'storage_ceiling','_Axis/Flags/host-storage')

    def commit(self, log):
        need(self.state['phase']=='initialized','phase',self.owner_name)
        need(re.fullmatch(r'_Axis/Logs/\d{4}(?:\.\d{2}){5}\.\d{3}Z\.md',log) and log==self.state['starting_log'],'starting_log','_Axis/Logs')
        self.guard();self.renew('_Axis/Flags/starting',self.read('_Axis/Flags/starting'))
        need(time.time()-self.path('_Axis/Flags/starting').stat().st_mtime<120,'starting_stale','_Axis/Flags/starting')
        self.tracking(True);self.validate_capabilities()
        need(self.read(log)==f'Session Starting\n\nby: Main Agent\nsession: {self.sid}\n','starting_log',log)
        self.owner_update(phase='committing')
        versions=re.findall(r'^current-version: (\S+)$',self.read('_Axis/CHANGELOG.md',optional=True,limit=4194304) or '',re.M)
        version_line=('axis-version: '+versions[0]+'\n') if len(versions)==1 else ''
        _,started=self.record('Logs',lambda _:f'Session Started\n\nby: Main Agent\nsession: {self.sid}\n'+version_line)
        self.owner_update(started_log=started)
        self.clear_flag('project-overlay')
        self.write_flag('session-id',self.sid+'\n'+stamp()+'\n')
        self.verify_session_id();self.guard()
        self.clear_flag('starting');self.release_admission(lease=True)
        remaining=self.read('_Axis/Flags/starting',optional=True)
        need(remaining is None or remaining.splitlines()[:1]==['cleared'],'completion','_Axis/Flags/starting')
        self.verify_session_id();need(not (self.root/self.claim_name).exists(),'completion',self.claim_name)
        return {'status':'committed','session':self.sid,'started_log':started}

    def verify_session_id(self):
        name='_Axis/Flags/session-id';lines=self.read(name).splitlines()
        need(len(lines)==2 and lines[0]==self.sid,'completion',name)
        need(parse_stamp(self.sid)<=parse_stamp(lines[1])<=dt.datetime.now(dt.timezone.utc) and time.time()-self.path(name).stat().st_mtime<60,'completion',name)

    def close(self):
        if self.owner_fd is not None:os.close(self.owner_fd);self.owner_fd=None

class Session(Startup):
    """Ordinary record creation after startup. The lease is the caller's own live, untombstoned Marker; there is no
    admission claim. Minting, claim, collision scan, exclusive create, read-back and Marker renewal are record()'s."""
    def __init__(self, root, session):
        super().__init__(root);parse_stamp(session)
        self.state={'session':session,'phase':'session'};self.lease=None

    def marker_body(self):return self.lease[0]

    def guard(self, starting=True, foreign=True):
        self.merge_access()
        if self.exists('_Axis/Agents/'+self.sid+'.kill'):raise Fault('lease_killed',self.marker_name)
        text=self.read(self.marker_name,optional=True)
        need(text is not None,'lease_missing',self.marker_name)
        info=self.path(self.marker_name).stat();lines=text.splitlines()
        if self.lease is None:
            main=lines[:1]==['Main: session']
            if main:need(len(lines)==4 and lines[1]=='' and lines[2]=='session: '+self.sid and lines[3].startswith('host: ') and lines[3][6:].strip(),'marker_invalid',self.marker_name)
            else:need(bool(lines) and lines[0].startswith(('External: ','Subagent: ')),'marker_invalid',self.marker_name)
            self.lease=(text,identity(info),main)
        need(text==self.lease[0] and identity(info)==self.lease[1],'marker_mismatch',self.marker_name)
        need(time.time()-info.st_mtime<3600,'lease_stale',self.marker_name)
        if self.lease[2]:need(not self.foreign_mains(),'foreign_main','_Axis/Agents')

    def track(self, kind, scope, text):
        """Append one current-time line to this session's telemetry, including its first line."""
        need(kind in ('INTENT','STATUS','ASK','REPLY','DONE'),'tracking_type')
        need(isinstance(scope,str) and 0<len(scope)<=1024 and not any(c in scope for c in '\r\n[]'),'tracking_scope')
        need(isinstance(text,str) and bool(text.strip()) and len(text.encode())<=4096 and not any(ord(c)<32 for c in text),'tracking_text')
        self.guard();relative='_Axis/Tracking/'+self.sid+'.md'
        path=self.path(relative,missing=True)
        fd=os.open(path,os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_NOFOLLOW,0o644)
        try:
            info=os.fstat(fd);regular(info,relative)
            if info.st_size:
                os.lseek(fd,-1,os.SEEK_END);need(os.read(fd,1)==b'\n','tracking_partial_line',relative)
            self.guard();now=stamp();line=f'{now} - {self.sid} - {kind} [{scope}] {text}\n';raw=line.encode()
            write_fd(fd,raw);os.fsync(fd)
            need(identity(path.stat())==identity(info),'tracking_replaced',relative)
            os.lseek(fd,-len(raw),os.SEEK_END);need(os.read(fd,len(raw))==raw,'tracking_readback',relative)
            self.guard()
            return {'status':'appended','path':relative,'timestamp':now,'type':kind}
        finally:os.close(fd)

    def memo(self, subject, content):
        need(isinstance(subject,str) and 0<len(subject)<=80 and subject.strip()==subject and not subject.endswith('.')
             and unicodedata.normalize('NFC',subject)==subject
             and not any(c in '/\\:*?"<>|' or unicodedata.category(c)=='Cc' for c in subject),'memo_subject')
        need(0<len(content.encode('utf-8'))<=65536,'record_size')
        self.guard();need(self.lease[2],'memo_main_only')
        self.path('_Memos',kind='directory')
        final,name=self.record('Memos',lambda _:content,memo_subject=subject)
        return {'status':'created','id':final,'path':name}

    def create(self, family, content):
        need(family in FAMILIES and family!='Status','family',family)
        need(family!='Agents' or content.startswith('Subagent: '),'family',family)
        lines=content.split('\n')
        need(0<len(content.encode('utf-8'))<=65536,'record_size')
        need(len(lines)>=2 and lines[0].strip() and len(lines[0])<=80 and lines[1]=='' and '\r' not in lines[0],'record_shape')
        self.guard()
        final,name=self.record(family,lambda _:content)
        return {'status':'created','id':final,'path':name}

class Parser(argparse.ArgumentParser):
    def error(self, message):raise Fault('arguments')

def body_input(path):
    """Read a record body from a file or stdin, bounded, strict UTF-8; nothing is written before this succeeds."""
    try:
        if path is None:data=sys.stdin.buffer.read(65537)
        else:
            with open(path,'rb') as handle:data=handle.read(65537)
        return data.decode('utf-8')
    except (OSError,UnicodeError):raise Fault('body') from None

def main():
    engine=None
    try:
        parser=Parser();parser.add_argument('--root',required=True);sub=parser.add_subparsers(dest='operation',required=True,parser_class=Parser)
        claim=sub.add_parser('claim');claim.add_argument('--initial',required=True);claim.add_argument('--host',required=True);claim.add_argument('--take-over',action='append',default=[])
        for name in ('initialize','record-capabilities','commit','check-indexes'):
            command=sub.add_parser(name);command.add_argument('--session',required=True);command.add_argument('--owner',required=True)
            if name=='commit':command.add_argument('--starting-log',required=True)
            if name=='record-capabilities':command.add_argument('--observations',required=True)
        record=sub.add_parser('record');record.add_argument('--session',required=True);record.add_argument('--family',required=True);record.add_argument('--body-file')
        memo=sub.add_parser('memo');memo.add_argument('--session',required=True);memo.add_argument('--subject',required=True);memo.add_argument('--body-file')
        track=sub.add_parser('track');track.add_argument('--session',required=True);track.add_argument('--type',choices=('INTENT','STATUS','ASK','REPLY','DONE'),required=True);track.add_argument('--scope',required=True);track.add_argument('--text',required=True)
        args=parser.parse_args()
        if fcntl is None or not hasattr(os,'O_NOFOLLOW') or os.utime not in os.supports_fd:
            print(json.dumps({'status':'unavailable','code':'platform'}));return 3
        if args.operation=='track':
            engine=Session(args.root,args.session);print(json.dumps(engine.track(args.type,args.scope,args.text),sort_keys=True));return 0
        if args.operation=='memo':
            content=body_input(args.body_file);engine=Session(args.root,args.session)
            print(json.dumps(engine.memo(args.subject,content),sort_keys=True));return 0
        if args.operation=='record':
            content=body_input(args.body_file);engine=Session(args.root,args.session)
            print(json.dumps(engine.create(args.family,content),sort_keys=True));return 0
        engine=Startup(args.root)
        if args.operation=='claim':
            for value in args.take_over:parse_stamp(value)
            result=engine.claim(args.initial,args.host,tuple(args.take_over))
        else:
            engine.load(args.session,args.owner,readonly=args.operation=='check-indexes')
            if args.operation=='initialize':result=engine.initialize()
            elif args.operation=='record-capabilities':result=engine.record_capabilities(args.observations)
            elif args.operation=='check-indexes':result=engine.check_indexes()
            else:result=engine.commit(args.starting_log)
        print(json.dumps(result,sort_keys=True));return 0
    except Fault as error:
        print(json.dumps({'status':'error','code':error.code,'path':error.path},sort_keys=True));return 2
    except (OSError,UnicodeError,ValueError,KeyError,TypeError):
        print(json.dumps({'status':'error','code':'io_or_record','path':''},sort_keys=True));return 2
    finally:
        if engine is not None:engine.close()

if __name__=='__main__':raise SystemExit(main())
