"""Per-output publisher gates; inventory completeness alone never clears a period."""

def require_period(metadata,family,year,month=None,uf=None):
    checks=metadata.get('publisher_periods',[])
    for record in checks:
        if record.get('family')!=family or record.get('year')!=year:continue
        if record.get('month')!=month:continue
        if uf is None and record.get('uf')!='all27':continue
        if uf is not None and record.get('uf') not in (uf,'all27'):continue
        if record.get('status')=='passed' and record.get('evidence'):
            return True
    raise ValueError('Requested publisher period is not verified; missing is not zero')
