import os,json,logging
from pathlib import Path
import redis
from .db import Session
from .models import Layout
from .selection import calculate
r=redis.Redis.from_url(os.environ['REDIS_URL'],decode_responses=True);Path('/artifacts').mkdir(exist_ok=True)
while True:
    Path('/tmp/worker-heartbeat').touch();entry=r.blpop('tunnel-selection',timeout=2)
    if not entry:continue
    with Session() as s:
        l=s.get(Layout,int(entry[1]))
        if not l or l.status!='calculating':continue
        try:
            calculate(s,l);l.status='ready';s.commit();Path(f'/artifacts/layout-{l.id}.json').write_text(json.dumps(l.evidence,ensure_ascii=False))
        except Exception as ex:
            s.rollback();l=s.get(Layout,int(entry[1]));l.status='failed';l.evidence={'error':str(ex)};s.commit();logging.exception('selection failed')
