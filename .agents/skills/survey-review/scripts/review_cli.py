#!/usr/bin/env python3
"""Minimal seven-record survey review CLI."""
import argparse,json,sys,hashlib
from datetime import date
from pathlib import Path
from pydantic import BaseModel,ConfigDict,Field
import review_support as base
class R(BaseModel): model_config=ConfigDict(extra='forbid')
class Context(R): paper_path:str='';sha256:str='';publication_date:date|None=None;date_basis:str='';version:str='';date_uncertainty:str=''
class Entry(R): id:str=''; data:dict=Field(default_factory=dict)
class Log(R): schema_version:int=2; conference:str='iclr'; context:Context=Field(default_factory=Context); contributions:list[Entry]=Field(default_factory=list); expectations:list[Entry]=Field(default_factory=list); evidence:list[Entry]=Field(default_factory=list); searches:list[Entry]=Field(default_factory=list); discoveries:list[Entry]=Field(default_factory=list); audits:list[Entry]=Field(default_factory=list); impacts:list[Entry]=Field(default_factory=list); review_outline:dict=Field(default_factory=lambda:{'summary':'','overall_score':None,'strengths':[],'weaknesses':[],'questions':[],'comments':[]}); overall_reason:str='';overall_refs:list[str]=Field(default_factory=list);scale_reason:str='';limitations:str=''
KINDS={'contribution':('contributions','K'),'expectation':('expectations','X'),'evidence':('evidence','E'),'search':('searches','S'),'discovery':('discoveries','D'),'audit':('audits','A'),'impact':('impacts','I')}
def out(a):
 if not a.dir: raise ValueError('--dir required')
 return Path(a.dir).resolve()
def load(p): return Log.model_validate_json((Path(p)/base.STATE_FILE).read_text(encoding='utf-8'))
def save(l,p): base.atomic_json(Path(p)/base.STATE_FILE,l.model_dump(mode='json'))
def init(a):
 src=base.resolve_input(a.paper); p=Path(a.dir).resolve() if a.dir else src.parent/f'review_{src.stem}'
 if p.name!=f'review_{src.stem}': raise ValueError('run folder must be review_<full input stem>')
 if p.exists() and any(p.iterdir()) and not a.force: raise ValueError('run folder exists')
 p.mkdir(parents=True,exist_ok=True);(p/'inputs').mkdir(exist_ok=True);(p/'sources').mkdir(exist_ok=True);text,sources=base.read_manuscript(src);(p/base.PAPER_FILE).write_text(text,encoding='utf-8')
 c=Context(paper_path=str((p/base.PAPER_FILE).resolve()),sha256=hashlib.sha256(text.encode()).hexdigest(),publication_date=a.publication_date,date_basis=a.date_basis,version=a.version,date_uncertainty=a.date_uncertainty);save(Log(conference=a.conference,context=c),p);base.atomic_json(p/'input_manifest.json',{'input':str(src),'sources':sources});print(p)
def put(a):
 p=out(a);l=load(p);field,prefix=KINDS[a.kind];raw=json.loads(Path(a.file).read_text(encoding='utf-8')); old=next((x for x in getattr(l,field) if x.id==raw.get('id')),None); ident=raw.get('id') or f'{prefix}{len(getattr(l,field))+1}'; obj=Entry(id=ident,data=raw); arr=getattr(l,field)
 if old: arr[arr.index(old)]=obj
 else: arr.append(obj)
 save(l,p);print(ident)
def audit(l,final=False):
 e=[]
 if final and (not l.context.paper_path or not l.review_outline.get('summary') or not l.overall_reason): e.append('final review needs context, summary and overall reason')
 known={x.id for n,_ in KINDS.values() for x in getattr(l,n)}
 for n,_ in KINDS.values():
  for x in getattr(l,n):
   for r in x.data.get('evidence_ids',[])+x.data.get('evidence_refs',[])+x.data.get('target_refs',[]):
    if r not in known:e.append(f'{x.id} references missing {r}')
 return sorted(set(e))
def main():
 p=argparse.ArgumentParser();p.add_argument('--dir');s=p.add_subparsers(dest='cmd',required=True);a=s.add_parser('init');a.add_argument('paper');a.add_argument('--dir',default=None);a.add_argument('--conference',default='iclr');a.add_argument('--force',action='store_true');a.add_argument('--publication-date',type=date.fromisoformat);a.add_argument('--date-basis',default='');a.add_argument('--version',default='');a.add_argument('--date-uncertainty',default='')
 x=s.add_parser('put');x.add_argument('kind',choices=KINDS);x.add_argument('--file',required=True)
 for n in ('judgment','context'):x=s.add_parser(n);x.add_argument('--file',required=True)
 x=s.add_parser('point');x.add_argument('--section',required=True);x.add_argument('--file',required=True)
 x=s.add_parser('outline');x.add_argument('--section',required=True);x.add_argument('--content',required=True)
 s.add_parser('audit');s.add_parser('finalize')
 a=p.parse_args()
 if a.cmd=='init':return init(a)
 l=load(out(a))
 if a.cmd=='put':return put(a)
 if a.cmd=='judgment':
  d=json.loads(Path(a.file).read_text(encoding='utf-8'));l.overall_reason=d['reason'];l.overall_refs=d.get('refs',[]);l.scale_reason=d.get('scale_reason','');l.limitations=d.get('limitations','')
 elif a.cmd=='point': l.review_outline.setdefault(a.section,[]).append(json.loads(Path(a.file).read_text(encoding='utf-8')))
 elif a.cmd=='outline': l.review_outline[a.section]=a.content if a.section=='summary' else float(a.content)
 elif a.cmd=='context': pass
 elif a.cmd in ('audit','finalize'):
  er=audit(l,a.cmd=='finalize');print(json.dumps({'errors':er}));
  if er:return 1
  if a.cmd=='finalize':(out(a)/base.REVIEW_FILE).write_text('# Survey review\n\n'+l.overall_reason,encoding='utf-8')
  return 0
 save(l,out(a))
if __name__=='__main__':
 try:sys.exit(main() or 0)
 except Exception as e:print(f'Error: {e}',file=sys.stderr);sys.exit(1)
