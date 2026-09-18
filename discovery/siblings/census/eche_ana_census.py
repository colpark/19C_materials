import json, re, sys, urllib.request, concurrent.futures as cf
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import rzip
rows = json.load(open(sys.argv[1]))
def files(rec):
    d = json.load(urllib.request.urlopen(urllib.request.Request(
        f"https://data.caltech.edu/api/records/{rec}/files", headers={"User-Agent": "curl/8"}), timeout=60))
    return [(e['key'], e['size']) for e in d['entries']]
def one(rec):
    out = dict(record=rec, title=rows[rec], anas=[])
    try:
        for key, size in files(rec):
            if not key.endswith('.zip') or size > 400e6 and False: continue
            try: z = rzip.open_remote(rec, key)
            except Exception as e: out.setdefault('errs', []).append(f'{key}:{e}'); continue
            anas = [n for n in z.namelist() if n.endswith('.ana')]
            if not anas: continue
            txt = z.read(anas[0]).decode('utf8', 'replace').replace('\r', '')
            if not re.search(r'^analysis_type: eche', txt, re.M): continue
            g = lambda k: (re.search(rf'^{k}: (.*)$', txt, re.M).group(1).strip() if re.search(rf'^{k}: (.*)$', txt, re.M) else None)
            foms = re.findall(r'^\s*(\S+\.csv): csv_fom_file;([^;\n]*);\d+;(\d+)', txt, re.M)
            # split into sub-analyses and collect samples for photo ones
            blocks = re.split(r'^(ana__\d+):\s*$', txt, flags=re.M)
            photo_samples = set(); photo_desc = []
            for i in range(1, len(blocks) - 1, 2):
                b = blocks[i + 1]
                d = re.search(r'^\s+description: (.*)$', b, re.M)
                d = d.group(1) if d else ''
                if 'photo' in d.lower() or 'illdiff' in d.lower():
                    photo_desc.append(d[:150])
                    photo_samples |= set(int(s) for s in re.findall(r';(\d+)\s*$', b, re.M) if len(s) >= 1 and int(s) > 0 and 'Sample' in b)
            samp2 = set()
            for fn in re.findall(r'^\s*(ana__\d+__Sample(\d+)_\S+?): ', txt, re.M):
                pass
            out['anas'].append(dict(key=key, size=size, plate_ids=g('plate_ids'), description=g('description'),
                experiment_path=g('experiment_path'), foms=[(a, b, int(c)) for a, b, c in foms],
                photo_desc=photo_desc,
                photo_samples=sorted(int(s) for s in set(re.findall(r'^\s*ana__\d+__Sample(\d+)_', txt, re.M))) if photo_desc else []))
    except Exception as e:
        out['error'] = str(e)
    return out
with cf.ThreadPoolExecutor(16) as ex:
    res = list(ex.map(one, list(rows)))
json.dump(res, open(sys.argv[2], 'w'), indent=1)
print(len(res), sum(1 for r in res if r.get('error')))
