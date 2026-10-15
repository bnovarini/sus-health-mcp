"""Private integer interval attack diagnostics, not a privacy certification."""
def propagate_total(bounds, total):
    """Narrow cell intervals using an independently known exact total."""
    if type(total) is not int or total < 0:
        raise ValueError('Nonnegative integer total required')
    out=[]
    for lo,hi in bounds:
        if type(lo) is not int or type(hi) is not int or lo<0 or hi<lo:
            raise ValueError('Invalid integer interval')
        out.append([lo,hi])
    if not sum(x[0] for x in out)<=total<=sum(x[1] for x in out):
        raise ValueError('Exact total inconsistent with intervals')
    changed=True
    while changed:
        changed=False
        lows=sum(x[0] for x in out);highs=sum(x[1] for x in out)
        for x in out:
            lo=max(x[0],total-highs+x[1]);hi=min(x[1],total-lows+x[0])
            if [lo,hi]!=x:
                x[:]=[lo,hi];changed=True
    return out


def intersect_revision(old,new,known_delta=0):
    """Narrow old and new values if an external exact cell change is known.

    A frozen release does not make subsequent revisions independent. This
    diagnostic assumes the supplied external delta is genuinely known.
    """
    if type(known_delta) is not int:
        raise ValueError('Integer delta required')
    for pair in (old,new):
        if len(pair)!=2 or any(type(x) is not int for x in pair) or not 0<=pair[0]<=pair[1]:
            raise ValueError('Invalid revision interval')
    low=max(old[0],new[0]-known_delta);high=min(old[1],new[1]-known_delta)
    if low>high:raise ValueError('Inconsistent external revision delta')
    return {'old':[low,high],'new':[low+known_delta,high+known_delta]}
