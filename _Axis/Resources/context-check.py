#!/usr/bin/env python3
"""Axis context check: prove that Axis guidance is still in context, and order a reload when it is not.

turn.py loads this file through importlib and prints the lines it returns; it is also a small CLI, run from the project root:
  python3 _Axis/Resources/context-check.py status   --session ID [--role R] [--gate] [--check on|off] FILE...
  python3 _Axis/Resources/context-check.py prove    --session ID [--role R] [--check on|off] [--no-write] --cid CID --answer 'a | b | c' FILE...
  python3 _Axis/Resources/context-check.py reloaded --session ID [--role R] [--check on|off] [--no-write] FILE...
  python3 _Axis/Resources/context-check.py corpus   FILE...
--observer replaces --session for an Observer, which has no Session ID and never writes. FILE... is the role's recovery
set in order: the core first, then the role file, then the rest; 'path > Heading' limits a file to one section, and the
caller resolves '@' entries (unresolved ones are dropped). State is _Temp/Context/{Session ID}.json, written only by
prove and reloaded; compaction marks are read from _Temp/Context/compactions.log. Exit 0 printed, proven or recorded;
10 check failed (reload listed); 2 refused (expired or reused check, malformed answer, reload not due): nothing written."""
import argparse,calendar,datetime as dt,errno,hashlib,json,os,random,re,stat,sys,time
from collections import Counter
from pathlib import Path

ENABLED=False  # 3.17 ships the check off: marks order a periodic reload instead (N12). Enablement follows R-check.
SCHEMA='axis.context-state/v1'
SKEW=300  # seconds a mark may run ahead of this clock before it is ignored
OPEN,WORDS,PASS,SLACK=6,8,7,4   # show 6 words; expect the next 8; pass at 7 in order; read at most 8+4 answer words
DRAW=0.5                         # random-draw probability per lease call
AGE,GATE_AGE,PERIOD=1800,600,1800
EXPIRY,TREADMILL,EPOCH_LIMIT=7200,900,3
MIN_REST,MARK_TAIL,KEEP_USED=50,65536,16
ID=re.compile(r'\d{4}(\.\d{2}){5}\.\d{3}Z')
WORD=re.compile(r'[A-Za-z0-9]+')
LINE_START=re.compile(r'[\s>#*+|_`\[("-]*(?:\d+[.)]\s+[\s*_`\[("]*)?')
SENTENCE_START=re.compile(r'[.!?|][*_`")\]]*\s+[*_`\[("]*$')
UNREAD='Practices and Commands read before this point count as unread: read each again before its next use.'

class Unsafe(Exception):
    """_Temp, _Temp/Context or the state file is linked or malformed: state is neither trusted nor written."""

def words(text):
    """Lowercase alphanumeric words; apostrophes and punctuation ignored."""
    return [w.lower() for w in WORD.findall(text.replace("'",'').replace('’',''))]

def ident(t):
    d=dt.datetime.fromtimestamp(t,dt.timezone.utc);return d.strftime('%Y.%m.%d.%H.%M.%S.')+'%03dZ'%(d.microsecond//1000)

def seconds(stamp):
    """Seconds since the epoch for a UTC identifier timestamp, else None."""
    if not isinstance(stamp,str) or not ID.fullmatch(stamp):return None
    p=[int(x) for x in stamp[:-1].split('.')]
    try:return calendar.timegm((p[0],p[1],p[2],p[3],p[4],p[5],0,0,0))+p[6]/1000
    except (ValueError,OverflowError):return None

# ---- corpus -----------------------------------------------------------------------------------------------------

def in_scope(rel):
    """A relative project path, or 'path > Heading' for one section, outside _Axis/Secrets/: never absolute or climbing.
    Other entries, such as unresolved '@' entries, are dropped from a set."""
    if not isinstance(rel,str) or not rel or rel.startswith(('/','@')) or '\\' in rel:return False
    parts=Path(rel.split(' > ',1)[0]).parts
    return '..' not in parts and parts[:2]!=('_Axis','Secrets')

def safe_read(root,rel):
    """Bytes of an in-scope project file, never through a link; None when refused or absent."""
    if not in_scope(rel):return None
    parts=Path(rel.split(' > ',1)[0]).parts;current=root
    try:
        for i,part in enumerate(parts):
            current=current/part;info=current.lstat()
            if stat.S_ISLNK(info.st_mode):return None
            if i<len(parts)-1 and not stat.S_ISDIR(info.st_mode):return None
        if not stat.S_ISREG(info.st_mode):return None
        return current.read_bytes()
    except OSError:return None

def section(text,heading):
    """The Markdown section under this heading, through the line before the next heading of its level or higher."""
    lines=text.split('\n');start=level=None;fence=False
    for i,line in enumerate(lines):
        if re.match(r'\s*(```|~~~)',line):fence=not fence
        m=None if fence else re.match(r'(#{1,6})\s+(.*?)\s*$',line)
        if m and start is None and m.group(2)==heading:start,level=i,len(m.group(1))
        elif m and start is not None and len(m.group(1))<=level:return '\n'.join(lines[start:i])
    return '\n'.join(lines[start:]) if start is not None else ''

def segments(text):
    """Runs of eligible prose: HTML comments, fenced blocks (the axis-role row included) and JSON rows are cut out,
    and a passage never spans a cut."""
    text=re.sub(r'<!--.*?(?:-->|\Z)','\n\x00\n',text.replace("'",'').replace('’',''),flags=re.S)
    out,run,fence,depth=[],[],None,0
    def close():
        if run:out.append('\n'.join(run));run.clear()
    for line in text.split('\n'):
        s=line.strip()
        if fence:
            if re.fullmatch(re.escape(fence[0])+'{%d,}'%len(fence),s):fence=None
            continue
        if depth:
            depth=max(0,depth+s.count('{')+s.count('[')-s.count('}')-s.count(']'));continue
        m=re.match(r'(`{3,}|~{3,})',s)
        if m:fence=m.group(1);close();continue
        if s=='\x00':close();continue
        if s.startswith('{') or s.startswith('[{') or s.startswith('["'):
            depth=max(0,s.count('{')+s.count('[')-s.count('}')-s.count(']'));close();continue
        run.append(line)
    close();return out

def tokens(segment):
    """(lowercase, original, starts a line or sentence, start offset, end offset) per word of one segment."""
    out=[]
    for m in WORD.finditer(segment):
        before=segment[segment.rfind('\n',0,m.start())+1:m.start()]
        out.append((m.group().lower(),m.group(),bool(LINE_START.fullmatch(before) or SENTENCE_START.search(before)),m.start(),m.end()))
    return out

def grams(seq):
    return {' '.join(seq[i:i+OPEN]) for i in range(len(seq)-OPEN+1)}

def build(root,files,entry=None):
    """The corpus of a recovery set: its digest, each file's 16-hex pin, and each file's eligible passages. A passage
    starts a line or sentence, has 14 words inside one segment with no table bar, opens with a 6-word sequence unique
    in the corpus, and shares no 6-word sequence with the entry file."""
    root=Path(root);files=[f for f in files if in_scope(f)];digest=hashlib.sha256();pins=[];segs=[]
    for rel in files:
        data=safe_read(root,rel);pin=hashlib.sha256(data).hexdigest() if data is not None else None
        digest.update(('%s\0%s\n'%(rel,pin or 'unavailable')).encode());pins.append(pin[:16] if pin else None)
        text=data.decode('utf-8','replace') if data is not None else ''
        if ' > ' in rel:text=section(text,rel.split(' > ',1)[1])
        segs.append([(s,tokens(s)) for s in segments(text)])
    banned=set()
    for rel in (entry if entry is not None else ('CLAUDE.md','AGENTS.md','GEMINI.md')):
        data=safe_read(root,rel)
        if data is not None:banned|=grams(words(data.decode('utf-8','replace')));digest.update(b'entry\0'+hashlib.sha256(data).digest())
    count=Counter(' '.join(w for w,*_ in t[i:i+OPEN]) for f in segs for _,t in f for i in range(len(t)-OPEN+1))
    eligible=[]
    for n,f in enumerate(segs):
        found=[]
        for k,(s,t) in enumerate(f):
            low=[w for w,*_ in t]
            for i in range(len(t)-OPEN-WORDS+1):
                if not t[i][2] or count[' '.join(low[i:i+OPEN])]!=1 or '|' in s[t[i][3]:t[i+OPEN+WORDS-1][4]]:continue
                if grams(low[i:i+OPEN+WORDS])&banned:continue
                found.append((n,k,i,tuple(o for _,o,*_ in t[i:i+OPEN]),tuple(low[i+OPEN:i+OPEN+WORDS])))
        eligible.append(found)
    return {'files':list(files),'pins':pins,'digest':digest.hexdigest(),'eligible':eligible}

def pick(corpus,cid,session):
    """Three passages, recomputed from the check ID: two from the core and one from the rest, or three from the core
    when the rest has fewer than 50 eligible passages. None when the corpus is too small."""
    rng=random.Random(int(hashlib.sha256(('%s\0%s\0%s'%(cid,session,corpus['digest'])).encode()).hexdigest(),16))
    core=corpus['eligible'][0] if corpus['eligible'] else [];rest=[p for f in corpus['eligible'][1:] for p in f]
    chosen=[]
    for pool in (core,core,rest if len(rest)>=MIN_REST else core):
        for j in rng.sample(range(len(pool)),min(len(pool),64)):
            p=pool[j]
            if not any(p[:2]==q[:2] and abs(p[2]-q[2])<OPEN+WORDS for q in chosen):chosen.append(p);break
        else:return None
    return chosen

def lcs(a,b):
    row=[0]*(len(b)+1)
    for x in a:
        prev=0
        for j,y in enumerate(b):
            prev,row[j+1]=row[j+1],(prev+1 if x==y else max(row[j+1],row[j]))
    return row[-1]

def verify(passage,answer):
    """At least 7 of the 8 expected words, in order. A repeated opening is ignored; '-' or an empty answer fails."""
    given=words(answer);opening=[w.lower() for w in passage[3]]
    if given[:OPEN]==opening:given=given[OPEN:]
    return lcs(given[:WORDS+SLACK],list(passage[4]))>=PASS

# ---- check IDs ----------------------------------------------------------------------------------------------------

def tag(minute,nonce,session,digest):
    return hashlib.sha256(('%s-%s\0%s\0%s'%(minute,nonce,session,digest)).encode()).hexdigest()[:4]

def new_cid(session,digest,now):
    minute='%x'%int(now//60);nonce=os.urandom(2).hex()
    return 'C-%s-%s%s'%(minute,nonce,tag(minute,nonce,session,digest))

def cid_valid(cid,session,digest,now):
    """Issued within 2 hours, for this session and this corpus digest."""
    m=re.fullmatch(r'C-([0-9a-f]{1,12})-([0-9a-f]{4})([0-9a-f]{4})',cid or '')
    if not m:return False
    age=int(now//60)-int(m.group(1),16)
    return 0<=age+1 and age*60<=EXPIRY and m.group(3)==tag(m.group(1),m.group(2),session,digest)

# ---- state and marks ------------------------------------------------------------------------------------------------

def context_dir(root,create=False):
    """_Temp/Context, or None when absent and not created. Raises Unsafe when either folder is linked or not a folder."""
    path=Path(root)
    for name in ('_Temp','Context'):
        path=path/name
        try:info=path.lstat()
        except FileNotFoundError:
            if not create:return None
            os.mkdir(path,0o700);info=path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):raise Unsafe(path.name)
    return path

def regular(path):
    """True for a single-link regular file; False when absent; Unsafe for a link or anything else."""
    try:info=path.lstat()
    except FileNotFoundError:return False
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise Unsafe(path.name)
    return True

def load(folder,session):
    if folder is None:return {}
    path=folder/(session+'.json')
    if not regular(path):return {}
    try:value=json.loads(path.read_bytes()[:65536].decode())
    except (OSError,ValueError):return {}
    return value if isinstance(value,dict) and value.get('schema')==SCHEMA and value.get('session')==session else {}

def save(root,session,state):
    """Create the state file exclusively, or replace it atomically through a same-folder temporary file."""
    folder=context_dir(root,create=True);path=folder/(session+'.json')
    body=(json.dumps(state,indent=1,sort_keys=True)+'\n').encode()
    flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0)
    target=path if not regular(path) else folder/('.%s.%s.tmp'%(session,os.urandom(4).hex()))
    fd=os.open(target,flags,0o600)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(body);stream.flush();os.fsync(stream.fileno())
        if target!=path:
            regular(path);os.replace(target,path)
    except BaseException:
        if target!=path:
            try:os.unlink(target)
            except OSError:pass
        raise

def marks(folder,session):
    """(time, own) for each well-formed compaction mark in the last 64 KB of the mark log. own is True when the mark's
    host session hash is bound to this Axis session, False when it is bound to another, and None for '-' or an unbound
    hash (unattributed)."""
    if folder is None:return []
    path=folder/'compactions.log'
    try:
        if not regular(path):return []
        with open(path,'rb') as stream:
            size=stream.seek(0,2);stream.seek(max(0,size-MARK_TAIL));lines=stream.read().decode('utf-8','replace').splitlines()
        if size>MARK_TAIL:lines=lines[1:]
    except OSError:return []
    out=[]
    for line in lines:
        part=line.split()
        if len(part)!=3 or not re.fullmatch(r'[0-9a-f]{12}|-',part[2]):continue
        when=seconds(part[0])
        if when is None:continue
        own=None
        if part[2]!='-':
            try:
                binding=folder/'bindings'/part[2]
                if not (folder/'bindings').is_symlink() and regular(binding):own=(binding.read_text().splitlines() or [''])[0].strip()==session
            except (OSError,Unsafe):own=None
        out.append((when,own))
    return out

# ---- output -------------------------------------------------------------------------------------------------------

def file_list(corpus,indexes):
    return ', '.join('%s (sha256 %s)'%(corpus['files'][i],corpus['pins'][i] or 'unavailable') for i in indexes)

def command(session):
    return 'python3 _Axis/Resources/turn.py '+('--observer' if session is None else '--session '+session)

def challenge(corpus,session,now):
    """(check ID, the three passages, the line asking for them), or None when the corpus is too small."""
    label=session or 'observer';cid=new_cid(label,corpus['digest'],now);chosen=pick(corpus,cid,label)
    if chosen is None:return None
    shown=' '.join('(%d) "%s"'%(n+1,' '.join(p[3])) for n,p in enumerate(chosen))
    return cid,chosen,('Handle before answering: context check - without opening or searching any file, give the 8 words after '
        'each opening: %s. Run: %s --prove %s \'a | b | c\' (no apostrophes; - for any you lack, expected after compaction).'
        %(shown,command(session),cid))

def unavailable():
    return 'Handle before answering: context check unavailable (core unreadable or too short); re-read your recovery set in full before relying on Axis guidance.'

def result(**fields):
    base={'code':0,'action':'none','reason':None,'lines':[],'tail':[],'reload':[],'cid':None,'status':None,'written':False}
    base.update(fields);return base

def fresh_state(session,role):
    return {'schema':SCHEMA,'session':session,'role':role,'epoch':0,'epoch_at':[],'fails_in_epoch':0,'last_result':None,
        'reload_pending':[],'proved_at':None,'corpus_digest':None,'mode':'check','last_reload':None,'last_mark_seen':None,
        'advised':False,'used':[]}

def open_state(root,session):
    """(folder, state, marks, warning line or None). An unsafe _Temp yields empty state and no marks."""
    try:folder=context_dir(root);return folder,load(folder,session),marks(folder,session),None
    except (Unsafe,OSError):return None,{},[],'Handle before answering: context state unverified (_Temp or _Temp/Context is linked or malformed); it is neither read nor written.'

def since(state,*keys):
    return max([seconds(state.get(k)) or 0 for k in keys])

def reload_mode(state,enabled):
    return state.get('mode')=='periodic-reload' or not enabled

def reload_due(state,mk,start,now):
    """Reason a reload is due in a reload mode: a mark newer than the last reload, or the period elapsed after one."""
    floor=max(start,since(state,'last_reload','last_mark_seen','proved_at'))
    if any(floor<t<=now+SKEW and mine is not False for t,mine in mk):return 'mark'  # not another session's, not future-dated
    last=seconds(state.get('last_reload'))
    if state.get('mode')=='periodic-reload' and last is not None and now-last>=PERIOD:return 'periodic'
    return None

def advise(state,role):
    """A one-time fresh-session line at epoch 3, or two epochs within 15 minutes."""
    at=[seconds(x) or 0 for x in state['epoch_at']]
    if state['advised'] or not (state['epoch']>=EPOCH_LIMIT or (len(at)>=2 and at[-1]-at[-2]<=TREADMILL)):return []
    state['advised']=True
    if role=='Main':return ['Context epoch %d: recommend a checkpointed fresh session once - finish this unit, run ^save, then ask the User for a new conversation.'%state['epoch']]
    return ['Context epoch %d: tell the User once that a fresh session is recommended, then continue.'%state['epoch']]

def new_epoch(state,now):
    state['epoch']+=1;state['epoch_at']=(state['epoch_at']+[ident(now)])[-4:];state['fails_in_epoch']=0

def persist(root,session,state,write):
    """(written, line). Never writes when write is False; a refused or unsafe write is reported, never raised."""
    if not write:return False,'Context state not recorded (read-only mode); the next turn checks again.'
    try:save(root,session,state);return True,None
    except Unsafe:return False,'Context state not recorded (_Temp or _Temp/Context is linked or malformed); the next turn checks again.'
    except OSError as e:
        why='read-only host' if isinstance(e,PermissionError) or e.errno in (errno.EROFS,errno.EPERM,errno.EACCES) else 'write failed'
        return False,'Context state not recorded (%s); the next turn checks again.'%why

# ---- public calls ---------------------------------------------------------------------------------------------------

def status(root,session,files,role=None,gate=False,enabled=None,observer=False,entry=None):
    """Lease-mode output. Writes nothing. A check is due on an unattributed or other session's mark newer than the last
    proof, at a proof age of 30 minutes (10 with gate; measured from session start before the first proof), or on a
    random draw with p = 1/2. A mark bound to this session orders the whole set's reload with a check that proves it."""
    enabled=ENABLED if enabled is None else enabled;now=time.time();root=Path(root);files=[f for f in files if in_scope(f)]
    if observer:
        if not enabled or random.random()>=DRAW:return result()
        corpus=build(root,files,entry);issued=challenge(corpus,None,now)
        return result(action='check',reason='draw',cid=issued and issued[0],lines=[issued[2] if issued else unavailable()])
    folder,state,mk,warning=open_state(root,session);head=[warning] if warning else []
    start=seconds(session) or now;proved=seconds(state.get('proved_at'));floor=max(proved or start,since(state,'last_mark_seen'))
    if reload_mode(state,enabled):
        why=reload_due(state,mk,start,now)
        if not why:return result(lines=head)
        corpus=build(root,files,entry);every=list(range(len(files)))
        line='Handle before answering: %s: read in full, through each end marker: %s; then run %s --reloaded.'%(
            'a compaction was recorded' if why=='mark' else 'periodic reload due',file_list(corpus,every),command(session))
        return result(action='reload',reason=why,reload=[files[i] for i in every],lines=head+[line,UNREAD])
    own=any(t>floor and mine for t,mine in mk)
    pending=[f for f in state.get('reload_pending',[]) if f in files] if state.get('last_result')=='fail' else []
    if own or pending:
        why,indexes='mark' if own else 'fail',list(range(len(files))) if own else [files.index(f) for f in pending]
    else:
        indexes=None
        if any(t>floor for t,_ in mk):why='mark'
        elif now-(proved or start)>=(GATE_AGE if gate else AGE):why='age'
        elif random.random()<DRAW:why='draw'
        else:return result(lines=head)
    corpus=build(root,files,entry);issued=challenge(corpus,session,now)
    if indexes is None:
        return result(action='check',reason=why,cid=issued and issued[0],lines=head+[issued[2] if issued else unavailable()])
    line='Handle before answering: %s: read in full, through each end marker: %s.'%(
        'context was compacted' if why=='mark' else 'context check failed',file_list(corpus,indexes))
    return result(action='reload',reason=why,reload=[files[i] for i in indexes],cid=issued and issued[0],
        lines=head+[line,UNREAD],tail=[issued[2] if issued else unavailable()])

def prove(root,session,cid,answer,files,role=None,enabled=None,observer=False,write=True,entry=None):
    """Verify three answers. Pass: CONTEXT OK, proof recorded. Fail: CONTEXT LOST, a graduated reload list (the core and
    the role file for a failed core passage, the failed file otherwise, the whole set on a second failure in the epoch)
    and a fresh check; a second failure in one epoch starts periodic-reload mode. Refused (code 2, nothing written):
    expired, reused or foreign check ID, or not exactly three answers."""
    enabled=ENABLED if enabled is None else enabled;now=time.time();root=Path(root);files=[f for f in files if in_scope(f)]
    label=None if observer else session;corpus=build(root,files,entry)
    if observer:folder,state,mk,warning=None,{},[],None
    else:folder,state,mk,warning=open_state(root,session)
    head=[warning] if warning else []
    if cid in state.get('used',[]) or not cid_valid(cid,label or 'observer',corpus['digest'],now):
        return result(code=2,lines=head+['CHECK EXPIRED: run turn.py again.'])
    parts=(answer or '').split('|')
    if len(parts)!=3:return result(code=2,lines=head+['CHECK REFUSED: give exactly three answers separated by |; nothing was recorded.'])
    chosen=pick(corpus,cid,label or 'observer')
    if chosen is None:return result(code=2,lines=head+[unavailable()])
    failed=[p for p,a in zip(chosen,parts) if not verify(p,a)]
    if observer:
        if not failed:return result(lines=['CONTEXT OK: 3 of 3.'])
        issued=challenge(corpus,None,now);every=list(range(len(files)))
        return result(code=10,action='reload',reason='fail',reload=list(files),cid=issued and issued[0],
            lines=['CONTEXT LOST: %d of 3 not in context.'%len(failed),'Reload: read in full, through each end marker, before answering: %s.'%file_list(corpus,every),UNREAD],
            tail=[issued[2] if issued else unavailable()])
    state={**fresh_state(session,role),**state,'role':role or state.get('role')}
    state['used']=(state['used']+[cid])[-KEEP_USED:]
    start=seconds(session) or now;newest=max([t for t,_ in mk if t<=now],default=None)
    floor=max(seconds(state.get('proved_at')) or start,since(state,'last_mark_seen'))
    extra=[];opened=False
    if any(mine and t>floor for t,mine in mk) and state['last_result']!='fail':
        new_epoch(state,now);opened=True;extra+=advise(state,role)  # a mark bound to this session is a detected loss
    if newest is not None:state['last_mark_seen']=ident(max(newest,seconds(state.get('last_mark_seen')) or 0))
    if not failed:
        status_text='epoch %d: reload proven'%state['epoch'] if state['last_result']=='fail' or opened else None
        state.update(last_result='pass',proved_at=ident(now),corpus_digest=corpus['digest'],reload_pending=[])
        written,note=persist(root,session,state,write)
        return result(lines=head+['CONTEXT OK: 3 of 3.']+extra+([note] if note else []),status=status_text,written=written)
    if state['last_result']!='fail' and not opened:new_epoch(state,now);extra+=advise(state,role)
    state['fails_in_epoch']+=1;state['last_result']='fail'
    periodic=state['fails_in_epoch']>=2 or state['mode']=='periodic-reload'
    if periodic:indexes=list(range(len(files)))
    elif any(p[0]==0 for p in failed):indexes=sorted({0,min(1,len(files)-1)}|{p[0] for p in failed})
    else:indexes=sorted({p[0] for p in failed})
    state['reload_pending']=[files[i] for i in indexes]
    lines=head+['CONTEXT LOST: %d of 3 not in context (context epoch %d).'%(len(failed),state['epoch']),
        'Reload: read in full, through each end marker, before answering: %s.'%file_list(corpus,indexes),UNREAD]
    if periodic:
        tail=['Periodic-reload mode: the reload list returns every 30 minutes and after any compaction mark; after each reload run %s --reloaded.'%command(session)]
        if role=='Main' and state['mode']!='periodic-reload':tail.append('Write a capability-downgrade Log naming your model: the context check failed again after a reload.')
        state.update(mode='periodic-reload',last_reload=ident(now),reload_pending=[]);issued=None
    else:
        issued=challenge(corpus,session,now);tail=[issued[2] if issued else unavailable()]
    written,note=persist(root,session,state,write)
    return result(code=10,action='reload',reason='fail',reload=[files[i] for i in indexes],cid=issued and issued[0],
        lines=lines+extra+([note] if note else []),tail=tail,written=written,
        status='epoch %d: check failed (%d/3); reload listed'%(state['epoch'],len(failed)))

def reloaded(root,session,files,role=None,enabled=None,write=True):
    """Record a reload in a reload mode (periodic-reload mode, or the check switched off after a mark). A bound mark
    acknowledged here is a detected loss and opens an epoch."""
    enabled=ENABLED if enabled is None else enabled;now=time.time();root=Path(root);files=[f for f in files if in_scope(f)]
    folder,state,mk,warning=open_state(root,session);head=[warning] if warning else []
    start=seconds(session) or now
    if not reload_mode(state,enabled) or (state.get('mode')!='periodic-reload' and not reload_due(state,mk,start,now)):
        return result(code=2,lines=head+['NOT NEEDED: --reloaded applies only in periodic-reload mode; answer the context check instead.'])
    state={**fresh_state(session,role),**state,'role':role or state.get('role')}
    floor=max(start,since(state,'last_reload','last_mark_seen','proved_at'));extra=[];opened=any(mine and t>floor for t,mine in mk)
    if opened:new_epoch(state,now);extra+=advise(state,role)
    newest=max([t for t,_ in mk if t<=now],default=None)
    if newest is not None:state['last_mark_seen']=ident(max(newest,seconds(state.get('last_mark_seen')) or 0))
    state.update(mode='periodic-reload',last_reload=ident(now),reload_pending=[])
    written,note=persist(root,session,state,write)
    return result(lines=head+['RELOAD RECORDED: the next reload is due in 30 minutes or after a compaction mark.']+extra+([note] if note else []),written=written,
        status='epoch %d: compaction mark; reload recorded'%state['epoch'] if opened else None)

def main(argv=None):
    a=argparse.ArgumentParser(description='Axis context check')
    a.add_argument('action',choices=('status','prove','reloaded','corpus'));a.add_argument('files',nargs='+')
    a.add_argument('--session');a.add_argument('--observer',action='store_true');a.add_argument('--role')
    a.add_argument('--gate',action='store_true');a.add_argument('--check',choices=('on','off'))
    a.add_argument('--no-write',action='store_true');a.add_argument('--cid');a.add_argument('--answer')
    a.add_argument('--entry',action='append')
    o=a.parse_intermixed_args(argv);root=Path.cwd().resolve();enabled=None if o.check is None else o.check=='on'
    if o.action=='corpus':
        c=build(root,o.files,o.entry)
        print('corpus %s: '%c['digest'][:16]+'; '.join('%s %d eligible'%(f,len(e)) for f,e in zip(c['files'],c['eligible'])));return 0
    if not o.observer and not (o.session and ID.fullmatch(o.session)):print('ERROR: not a Session ID.');return 2
    if o.action=='status':r=status(root,o.session,o.files,o.role,o.gate,enabled,o.observer,o.entry)
    elif o.action=='prove':
        if not o.cid or o.answer is None:print('ERROR: prove needs --cid and --answer.');return 2
        r=prove(root,o.session,o.cid,o.answer,o.files,o.role,enabled,o.observer,not (o.no_write or o.observer),o.entry)
    elif o.observer:print('ERROR: an Observer records no reload.');return 2
    else:r=reloaded(root,o.session,o.files,o.role,enabled,not o.no_write)
    for line in r['lines']+r['tail']:print(line)
    return r['code']

if __name__=='__main__':sys.exit(main())
