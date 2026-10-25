#!/usr/bin/env python3
"""Read-only feedback draft format validation. No network, authentication or sending.

This checks structure, not factual truth, redaction quality or User authorization.
"""
import argparse,json,re,sys
from pathlib import Path
HEADER=('axis-feedback','kind','axis-version','latest-release','host','harness','model','os','shell','context-management','permissions','storage-policy','max-concurrent-sessions','reproduced','reproduced-on-latest','duplicates','redaction','delivery','prepared')
FIELDS={
 'bug':('Axis report header','Axis version','Bug type','Summary','Steps to reproduce','Expected','Actual','Host and model','Operating system','Reproduction and latest-release check','Related issues searched','Analysis (not verified)','Confirmations'),
 'feature':('Axis report header','Axis version','Problem','Requested change','Current workaround','Related issues or discussions searched','Analysis (not verified)','Confirmations')}
BUG_TYPES=('Wrong behavior','Regression (worked in an earlier version)','Crash or stop','Records damaged or lost','Documentation wrong')
CONFIRMATIONS={'bug':('This report contains no secrets, personal data or private project content.','This is not a security vulnerability.'),'feature':('This request contains no secrets, personal data or private project content.',)}
def check(text,kind):
 errors=[];matches=[];fence=None
 for index,line in enumerate(text.splitlines()):
  f=re.match(r'^(`{3,}|~{3,})',line)
  if f:
   token=f[1]
   if fence is None:fence=token[0],len(token)
   elif token[0]==fence[0] and len(token)>=fence[1] and line[len(token):].strip()=='':fence=None
   continue
  if fence is None and re.match(r'^#{1,6}\s',line):matches.append((index,line))
 if fence is not None:errors.append('unclosed code fence')
 expected=['### '+field for field in FIELDS[kind]]
 if [line for _,line in matches]!=expected:return errors+['headings must be level three, in exact form order, with Confirmations last']
 lines=text.splitlines();sections={FIELDS[kind][i]:'\n'.join(lines[start+1:matches[i+1][0] if i+1<len(matches) else len(lines)]).strip() for i,(start,_) in enumerate(matches)}
 header=re.fullmatch(r'```(?:text)?\n(.*?)\n```',sections['Axis report header'],re.S)
 if not header:errors.append('header must be a fenced text block')
 else:
  fields=[];values={}
  for line in header[1].splitlines():
   pair=line.split(': ',1)
   if len(pair)!=2 or not pair[1].strip():errors.append('header fields need nonempty single-line values');continue
   fields.append(pair[0]);values[pair[0]]=pair[1]
  if tuple(fields)!=HEADER:errors.append('header fields must appear exactly once in contract order')
  if values.get('axis-feedback')!='1' or values.get('kind')!=kind:errors.append('header version/kind mismatch')
  if values.get('delivery') not in ('gh','link','draft'):errors.append('delivery must be gh, link or draft')
  if values.get('redaction')!='checked':errors.append('redaction check must be recorded')
  if values.get('reproduced') not in ('yes','partly','no','not-attempted','unknown'):errors.append('invalid reproduced value')
  if not re.fullmatch(r'none-found|not-searched|#\d+(?: #\d+)*',values.get('duplicates','')):errors.append('invalid duplicates value')
 if kind=='bug' and sections['Bug type'] not in BUG_TYPES:errors.append('Bug type must be one exact form choice')
 required=('Axis version','Summary','Steps to reproduce','Expected','Actual','Host and model','Operating system') if kind=='bug' else ('Axis version','Problem','Requested change')
 if any(not sections[x] for x in required):errors.append('required form field is empty')
 if sections['Confirmations'].splitlines()!=['- [x] '+x for x in CONFIRMATIONS[kind]]:errors.append('confirmations must match the form and be reviewed before validation')
 return errors

def main():
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=FIELDS,required=True);p.add_argument('--draft',required=True);a=p.parse_args()
 try:
  with Path(a.draft).open('rb') as handle:raw=handle.read(131073)
  if len(raw)>131072:raise ValueError('draft exceeds 128 KiB')
  errors=check(raw.decode('utf-8'),a.kind)
 except (OSError,UnicodeError,ValueError) as e:print(json.dumps({'status':'invalid','errors':[type(e).__name__]}));return 2
 print(json.dumps({'status':'valid' if not errors else 'invalid','errors':errors}));return 1 if errors else 0
if __name__=='__main__':sys.exit(main())
