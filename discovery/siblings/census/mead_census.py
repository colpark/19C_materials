"""Census one MEAD CaltechDATA bundle record without downloading raw data: list every zip via
HTTP range requests, read .ana/.exp/.rcp text and the small FOM csv files."""
import sys, json, re, io, collections, urllib.request
import pandas as pd
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import rzip

def files(rec):
    d = json.load(urllib.request.urlopen(urllib.request.Request(f"https://data.caltech.edu/api/records/{rec}/files", headers={"User-Agent": "curl/8"}), timeout=60))
    return [(e['key'], e['size']) for e in d['entries']]

def census(rec):
    out = dict(record=rec, zips=[], xrd_samples=set(), xrd_ana=[], photo=[], eche_conditions=[], errors=[])
    for key, size in files(rec):
        if not key.endswith('.zip'):
            continue
        try:
            z = rzip.open_remote(rec, key)
        except Exception as e:
            out['errors'].append(f"{key}: {e}"); continue
        names = z.namelist()
        kind = None
        anas = [n for n in names if n.endswith('.ana')]
        rcps = [n for n in names if n.endswith('.rcp')]
        exps = [n for n in names if n.endswith('.exp')]
        info = dict(key=key, size=size, n=len(names))
        if anas:
            txt = z.read(anas[0]).decode('utf8', 'replace')
            at = re.search(r'analysis_type: (\S+)', txt)
            info['analysis_type'] = at.group(1) if at else None
            if info['analysis_type'] in ('xrds', 'ssrl'):
                samp = re.findall(r'xrds_csv_pattern_file;[^;]*;\d+;\d+;(\d+)', txt) or \
                       re.findall(r'pattern_file[^\n]*;(\d+)\s*$', txt, re.M)
                out['xrd_samples'].update(int(s) for s in samp)
                out['xrd_ana'].append(dict(key=key, n_patterns=len(set(samp)), desc=re.search(r'description: (.*)', txt).group(1)[:200]))
            elif info['analysis_type'] == 'eche':
                for n in names:
                    if n.endswith('.csv') and 'photo' in n:
                        try:
                            raw = z.read(n).decode('utf8', 'replace').splitlines()
                            hdr = [i for i, l in enumerate(raw) if l.startswith('sample_no')]
                            df = pd.read_csv(io.StringIO('\n'.join(raw[hdr[0]:]))) if hdr else None
                            out['photo'].append(dict(key=key, file=n, n_rows=0 if df is None else len(df),
                                                     samples=[] if df is None else df['sample_no'].astype(int).tolist(),
                                                     cols=[] if df is None else list(df.columns)))
                        except Exception as e:
                            out['errors'].append(f"{key}/{n}: {e}")
                m = re.search(r'experiment_path: (.*)', txt)
                info['experiment_path'] = m.group(1) if m else None
        if rcps:
            txt = z.read(rcps[0]).decode('utf8', 'replace')
            tn = re.search(r'technique_name: (\S+)', txt)
            info['technique'] = tn.group(1) if tn else None
            if info['technique'] == 'eche':
                c = {k: (re.search(rf'^{k}: (.*)$', txt, re.M).group(1) if re.search(rf'^{k}: (.*)$', txt, re.M) else None)
                     for k in ['solution_ph', 'solution_description', 'illumination_wavelength', 'illumination_intensity', 'reference_vrhe', 'experiment_params_vi_path']}
                c['key'] = key
                out['eche_conditions'].append(c)
            if info['technique'] == 'xrds':
                info['xrd_raw_samples'] = sorted(set(re.findall(r'xrds_bruker_gfrm_file;(\d+)', txt)))
        if exps:
            txt = z.read(exps[0]).decode('utf8', 'replace')
            et = re.search(r'experiment_type: (\S+)', txt)
            info['experiment_type'] = et.group(1) if et else None
        out['zips'].append(info)
    out['xrd_samples'] = sorted(out['xrd_samples'])
    return out

if __name__ == '__main__':
    rec = sys.argv[1]
    r = census(rec)
    json.dump(r, open(sys.argv[2], 'w'), indent=1, default=str)
    photo_samples = set(s for p in r['photo'] for s in p['samples'])
    print(rec, 'xrd_samples', len(r['xrd_samples']), 'photo_fom_files', len(r['photo']), 'photo_samples', len(photo_samples),
          'pH', sorted(set(c['solution_ph'] for c in r['eche_conditions'] if c['solution_ph'])), 'errors', len(r['errors']))
