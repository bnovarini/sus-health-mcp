"""Private phase 1 API facade. Importing this module starts no server."""
import pathlib,json,threading
from contextlib import contextmanager
from .foundation import References,ReleasedCells,resolve_code
from .json_cells import ReleasedJSON
from .methods import Methods
from .exporter import export_released
class FoundationAPI:
 def __init__(self,reference_root,artifact_root,coverage_snapshot):
  self.refs=References(reference_root);self.root=pathlib.Path(artifact_root);self.methods=Methods(coverage_snapshot);self.snapshot=self.methods.snapshot;self.readers={};self._work=threading.BoundedSemaphore(1)
 @contextmanager
 def work_slot(self):
  if not self._work.acquire(blocking=False):raise ValueError('Another dataset query or export is running;retry after it completes')
  try:yield
  finally:self._work.release()
 def lookup(self,kind,query='',vintage='',municipality='',limit=30,cursor=''):
  return self.refs.lookup(kind,query,vintage,municipality,limit,cursor)
 def resolve(self,kind,code,vintage='202608'):return resolve_code(self.refs.root,kind,code,vintage)
 def reader(self,kind):
  if kind in self.readers:return self.readers[kind]
  if kind=='clinical':
   m=self.snapshot['SUS_CLINICAL_DATA']['clinical-metadata.json'];r=ReleasedCells(pathlib.Path(__import__('os').environ['SUS_CLINICAL_DATA'])/'clinical.parquet',m['clinical_sha256'],m['release_id'],kind,m)
  elif kind=='capacity':
   m=self.snapshot['SUS_STAGED_DATA']['metadata.json'];r=ReleasedCells(pathlib.Path(__import__('os').environ['SUS_STAGED_DATA'])/'capacity.parquet',m['capacity_sha256'],m['release_id'],kind,m)
  elif kind in ['known_care','deeper']:
   env='SUS_KNOWN_CARE_DATA' if kind=='known_care' else 'SUS_DEEPER_DATA';filename='known-care.json' if kind=='known_care' else 'surface-intervals.json';m=self.snapshot[env]['known-care-metadata.json' if kind=='known_care' else 'metadata.json'];r=ReleasedJSON(pathlib.Path(__import__('os').environ['SUS_KNOWN_CARE_DATA' if kind=='known_care' else 'SUS_DEEPER_DATA'])/filename,m['known_care_sha256' if kind=='known_care' else 'artifact_sha256'],m['release_id'],kind,m)
  else:raise ValueError('Unknown frozen output')
  self.readers[kind]=r;return r
 def page(self,kind,query,limit=100,cursor=''):
  with self.work_slot():return self.reader(kind).page(**query,limit=limit,cursor=cursor)
 def research_methods(self,kind,query):
  with self.work_slot():
   self.reader(kind).page(**query,limit=1)
   return self.methods.describe(kind,query)
 def export(self,kind,query,path):
  with self.work_slot():
   methods=self.methods.describe(kind,query);methods['label_reference']={'sha256':self.refs.meta['sha256'],'months':self.refs.meta.get('historical_periods',self.refs.meta.get('periods',[])),'meaning':'Reference labels only;annual processing-file cohorts cannot pick a single monthly code-validity vintage. Auxiliary/current labels are explicitly distinguished from dated definitions.'};return export_released(self.reader(kind),path,query,methods)
 def coverage(self):
  s=self.snapshot
  return {'clinical':{k:v for k,v in s['SUS_CLINICAL_DATA']['clinical-metadata.json'].items() if k in ['release_id','years','approved_scopes','preview_scopes','warnings','clinical_sha256','grain']},'registry':{k:v for k,v in s['SUS_STAGED_DATA']['metadata.json'].items() if k in ['release_id','registry_years','registry_partial_years','registry_warnings','coverage','publisher_periods','gaps','capacity_sha256']},'reference':self.refs.meta,'candidate_status':'phase1_active;exports_owner_only;no_new_clinical_tables','new_clinical_tables':False,'new_totals':False,'recurring_cost_increase':False}
