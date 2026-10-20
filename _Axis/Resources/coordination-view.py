#!/usr/bin/env python3
"""Read-only compact coordination view; cached rows are never authority. No model or network."""
from pathlib import Path
import argparse,json,os,re,stat,sys
LIMIT=65536

def read(root,name):
 p=root/name;current=Path(root.anchor)
 for part in root.parts[1:]:
  current/=part
  if current.is_symlink():raise ValueError('unsafe root path')
 current=root
 for part in Path(name).parts:
  current/=part
  if current.is_symlink():raise ValueError('unsafe view path')
 fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  info=os.fstat(fd)
  if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>LIMIT:raise ValueError('unsafe/oversize view')
  data=os.read(fd,LIMIT+1)
  if len(data)>LIMIT:raise ValueError('oversize view')
  return data.decode('utf-8')
 finally:os.close(fd)

def summary(root):
 root=Path(root).absolute();result={'verification':'cached-unverified','indexes':{},'submissions':0,'legacy_requests':0,'warnings':[]}
 for family in ('Teams','Messages','Jobs','Schedules'):
  name='_Axis/'+family.upper()+'.md'
  try:
   text=read(root,name);rows=[]
   for line in text.splitlines():
    if line.startswith('| ['):
     cells=[v.strip() for v in line.strip('|').split('|')]
     if len(cells)>=3:rows.append({'record':cells[0],'subject':cells[1],'state':cells[2]})
   total=re.search(r'^total-count: ([0-9]+)$',text,re.M)
   total_records=int(total[1]) if total else len(rows)
   result['indexes'][family]={'rows':rows[:100],'total_rows':len(rows),'total_records':total_records,'truncated':total_records>len(rows),'verification':'cached-unverified'}
   if family=='Messages':
    m=re.search(r'^pending-count: ([0-9]+)$',text,re.M);result['pending_messages']=int(m[1]) if m else len(rows)
  except FileNotFoundError:result['indexes'][family]={'rows':[],'total_rows':0,'verification':'absent'}
  except (OSError,ValueError,UnicodeError):result['warnings'].append(family+' index unavailable')
 for family,key in [('Submissions','submissions'),('Requests','legacy_requests')]:
  path=root/'_Axis'/family
  try:
   if path.is_symlink():raise ValueError('unsafe queue')
   count=0
   if path.exists():
    with os.scandir(path) as entries:
     for entry in entries:
      if family=='Submissions' and entry.name=='_received' and entry.is_dir(follow_symlinks=False):continue
      if family=='Submissions' and entry.name in ('_migration.md','_migration-complete.md') and entry.is_file(follow_symlinks=False):continue
      if entry.name=='.gitkeep' and entry.is_file(follow_symlinks=False):continue
      count+=1
      if count>=1000:result['warnings'].append(family+' inventory capped');break
      if entry.is_symlink() or not entry.is_file(follow_symlinks=False):result['warnings'].append(family+' unsafe entry')
   result[key]=count
  except (OSError,ValueError):result['warnings'].append(family+' unavailable')
 result.setdefault('pending_messages',0)
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args();print(json.dumps(summary(a.root)))
if __name__=='__main__':main()
