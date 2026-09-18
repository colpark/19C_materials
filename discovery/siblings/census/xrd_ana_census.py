"""For every MEAD 'X-ray diffraction analysis' / 'Synchrotron x-ray diffraction analysis' record, read
the .ana inside each zip by HTTP range requests: plate ids, analysis description, sample numbers with a
pattern file."""
import json, re, sys, urllib.request, concurrent.futures as cf
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import rzip

rows = json.load(open(sys.argv[1]))
todo = [i for i, t in rows.items() if 'diffraction analysis in which' in t]

def files(rec):
    d = json.load(urllib.request.urlopen(urllib.request.Request(
        f"https://data.caltech.edu/api/records/{rec}/files", headers={"User-Agent": "curl/8"}), timeout=60))
    return [(e['key'], e['size']) for e in d['entries']]

def one(rec):
    out = dict(record=rec, title=rows[rec], zips=[])
    try:
        for key, size in files(rec):
            if not key.endswith('.zip'):
                out['zips'].append(dict(key=key, size=size)); continue
            z = rzip.open_remote(rec, key)
            names = z.namelist()
            anas = [n for n in names if n.endswith('.ana')]
            info = dict(key=key, size=size, n_files=len(names))
            if anas:
                txt = z.read(anas[0]).decode('utf8', 'replace')
                g = lambda k: (re.search(rf'^{k}: (.*)$', txt, re.M).group(1).strip() if re.search(rf'^{k}: (.*)$', txt, re.M) else None)
                info.update(plate_ids=g('plate_ids'), analysis_type=g('analysis_type'), description=g('description'),
                            experiment_path=g('experiment_path'))
                samp = [m[1] for m in re.findall(r'^\s*(\S+): (\w*(?:pattern|integrated|1d)\w*);[^\n]*?;(\d+)\s*$', txt.replace('\r', ''), re.M)] if False else [m[2] for m in re.findall(r'^\s*(\S+): (\w*(?:pattern|integrated|1d)\w*);[^\n]*?;(\d+)\s*$', txt.replace('\r', ''), re.M)]
                info['pattern_samples'] = sorted(set(int(s) for s in samp))
                info['file_kinds'] = sorted(set(re.findall(r': (\w+_file);', txt)))
            out['zips'].append(info)
    except Exception as e:
        out['error'] = str(e)
    return out

with cf.ThreadPoolExecutor(12) as ex:
    res = list(ex.map(one, todo))
json.dump(res, open(sys.argv[2], 'w'), indent=1)
for r in res:
    for z in r['zips']:
        if z.get('plate_ids'):
            print(r['record'], z.get('plate_ids'), z.get('analysis_type'), len(z.get('pattern_samples', [])), (z.get('description') or '')[:80])
    if r.get('error'): print(r['record'], 'ERROR', r['error'][:100])
