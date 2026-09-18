"""Remote zip listing/reading over HTTP range requests (CaltechDATA -> OSN redirect)."""
import io, json, subprocess, zipfile, urllib.request, functools

class HttpFile(io.RawIOBase):
    def __init__(self, url):
        req = urllib.request.Request(url, headers={"Range": "bytes=0-0", "User-Agent": "curl/8"})
        r = urllib.request.urlopen(req, timeout=60)
        self.url = r.geturl()
        self.size = int(r.headers["Content-Range"].split("/")[1]); r.read()
        self.pos = 0
        self.cache = {}
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        if whence == 0: self.pos = off
        elif whence == 1: self.pos += off
        else: self.pos = self.size + off
        return self.pos
    def read(self, n=-1):
        if n is None or n < 0: n = self.size - self.pos
        if n == 0 or self.pos >= self.size: return b""
        end = min(self.size, self.pos + n) - 1
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={self.pos}-{end}", "User-Agent": "curl/8"})
        for attempt in range(4):
            try:
                data = urllib.request.urlopen(req, timeout=120).read(); break
            except Exception:
                if attempt == 3: raise
        self.pos += len(data)
        return data
    def readinto(self, b):
        d = self.read(len(b)); b[:len(d)] = d; return len(d)

def open_remote(record, key):
    url = f"https://data.caltech.edu/records/{record}/files/{key}?download=1"
    return zipfile.ZipFile(io.BufferedReader(HttpFile(url), buffer_size=1 << 16))
