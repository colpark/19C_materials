import json, re, sys, urllib.request, concurrent.futures as cf
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import rzip
rows = json.load(open(sys.argv[1]))
def files(rec):
    d = json.load(urllib.request.urlopen(urllib.request.Request(f"https://data.caltech.edu/api/records/{rec}/files", headers={"User-Agent": "curl/8"}), timeout=60))
    return [(e['key'], e['size']) for e in d['entries']]
def one(rec):
    out = dict(record=rec, anas=[])
    try:
        for key, size in files(rec):
            if not key.endswith('.zip'): continue
            z = rzip.open_remote(rec, key)
            anas = [n for n in z.namelist() if n.endswith('.ana')]
            if not anas: continue
            txt = z.read(anas[0]).decode('utf8', 'replace').replace('\r', '')
            at = re.search(r'^analysis_type: (\S+)', txt, re.M)
            if not at or at.group(1) != 'xrfs': continue
            pid = re.search(r'^plate_ids: (.*)$', txt, re.M)
            foms = re.findall(r'^\s*(\S+\.csv): csv_fom_file;([^;\n]*);\d+;(\d+)', txt, re.M)
            out['anas'].append(dict(key=key, plate_ids=pid.group(1) if pid else None, foms=[(a, b[:200], int(c)) for a, b, c in foms]))
    except Exception as e:
        out['error'] = str(e)
    return out
with cf.ThreadPoolExecutor(16) as ex:
    res = list(ex.map(one, list(rows)))
json.dump(res, open(sys.argv[2], 'w'), indent=1)
print(len(res), sum(1 for r in res if r.get('error')))
