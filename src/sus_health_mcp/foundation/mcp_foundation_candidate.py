"""MCP registration. No listener,public route or deployment on import."""
from typing import Literal,Union,Annotated
from pydantic import BaseModel,ConfigDict,Field
class StrictModel(BaseModel):
 model_config=ConfigDict(extra='forbid',strict=True)
class ClinicalQuery(StrictModel):
 kind:Literal['clinical']
 uf:str
 year:int
 family:Literal['RD','PA','AM','DO']
 municipality:str=''
 cid_prefix:str=''
class RegistryQuery(StrictModel):
 kind:Literal['capacity']
 uf:str
 year:int
 family:Literal['ST','LT','SR','HB']
 month:int
 municipality:str=''
 registry_code_prefix:str=''
class KnownCareQuery(StrictModel):
 kind:Literal['known_care']
 uf:str
 year:int
 view:Literal['residence','flows']
 municipality:str=''
class DeeperQuery(StrictModel):
 kind:Literal['deeper']
 uf:str
 year:int
 surface:Literal['related_E85_separateCID','tafamidis61_billing_allCID','nonspecific_workup_separateprocedure']
 municipality:str=''
Query=Annotated[Union[ClinicalQuery,RegistryQuery,KnownCareQuery,DeeperQuery],Field(discriminator='kind')]
Kind=Literal['cid','procedure','service','service_class','authorization','bed_detail','facility','municipality','facility_type','cnes_bed_type','cnes_bed_specialty']
def register(mcp,api):
 @mcp.tool()
 def reference_lookup(kind:Kind,query:str='',vintage:str='',municipality:str='',limit:int=30,cursor:str='')->dict:
  """Dated code/name lookup. Show ambiguous matches;not historical identity or clinical eligibility."""
  return api.lookup(kind,query,vintage,municipality,limit,cursor)
 @mcp.tool()
 def reference_resolve(kind:Kind,code:str,vintage:str='202608')->dict:
  """Exact source-code label,with dated/auxiliary/unmapped status. Never recodes source data."""
  return api.resolve(kind,code,vintage)
 @mcp.tool()
 def released_cells_page(query:Query,limit:int=100,cursor:str='')->dict:
  """Page existing frozen cells only. Cursors bind query/artifact;no new totals. Missing is unknown."""
  d=query.model_dump();kind=d.pop('kind');return api.page(kind,d,limit,cursor)
 @mcp.tool()
 def research_methods(query:Query)->dict:
  """Query,release,unit,time basis,source gaps and limits for the frozen output. Not patient research."""
  d=query.model_dump();kind=d.pop('kind');return api.research_methods(kind,d)
 @mcp.tool()
 def foundation_coverage()->dict:
  """Reference vintages,source coverage,preliminary data and unavailable periods. Call before research."""
  return api.coverage()
 if hasattr(mcp,'_tool_manager'):
  for t in mcp._tool_manager.list_tools():
   if t.name in ['reference_lookup','reference_resolve','released_cells_page','research_methods','foundation_coverage']:
    t.fn_metadata.arg_model.model_config={**t.fn_metadata.arg_model.model_config,'extra':'forbid','strict':True};t.fn_metadata.arg_model.model_rebuild(force=True);t.parameters=t.fn_metadata.arg_model.model_json_schema()
 # Complete exports remain local/private;publication is an owner-reviewed action.
