"""Öppen ordbas för King of Parsing.

Glosor:   STEPBible TBESG (Tyndale House Cambridge / STEPBible.org, CC BY 4.0),
          som bygger på Abbott-Smith och Middle Liddell.
Strong's: MACULA Greek (Biblica / Clear, CC BY 4.0), används för att hitta rätt
          TBESG-post när uppslagsformen skiljer sig (t.ex. ἀπόλλυμι/ἀπολλύω).
Rättelser: scripts/glosor_rattelser.tsv (projektets egna glosor).
Uppslagsform för substantiv (genitiv och genus) räknas fram ur MorphGNT."""
import os,re,csv,collections,urllib.request,unicodedata as u

TBESG_URL=("https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Lexicons/"
           "TBESG%20-%20Translators%20Brief%20lexicon%20of%20Extended%20Strongs%20for%20Greek%20-%20STEPBible.org%20CC%20BY.txt")
MACULA_URL="https://raw.githubusercontent.com/Clear-Bible/macula-greek/main/SBLGNT/tsv/macula-greek-SBLGNT.tsv"

def nfc(s): return u.normalize('NFC',s.strip())
def strip(s): return ''.join(c for c in u.normalize('NFD',s) if not u.combining(c)).lower()

def _fetch(url,path):
    if not os.path.exists(path):
        print("Laddar ned",os.path.basename(path),"…")
        tmp=path+".part"
        with urllib.request.urlopen(url) as r, open(tmp,"wb") as f: f.write(r.read())
        os.replace(tmp,path)
    return path

def _clean(g,t):
    """Gör om en TBESG-glosa till appens format: 'to write', 'spirit, breath'."""
    g=g.split(':')[0].strip()
    g=re.sub(r'\s*/\s*',', ',g)
    if t=='N': g=re.sub(r'^(a|an|the)\s+','',g)
    if t=='V' and g and not g.startswith('to ') and re.match(r'^[a-z]',g) and not g.endswith('!'):
        g='to '+g
    return g

class Lexikon:
    def __init__(self,cache,morph_lines,rattelser=None):
        self._tbesg(_fetch(TBESG_URL,os.path.join(cache,"tbesg.txt")))
        self._macula(_fetch(MACULA_URL,os.path.join(cache,"macula-greek-SBLGNT.tsv")))
        self._morph(morph_lines)
        self.fix={}; self.fixw={}
        if rattelser and os.path.exists(rattelser):
            for r in csv.DictReader(open(rattelser,encoding="utf8"),delimiter="\t"):
                h=nfc(r.get("uppslagsord") or "")
                if h and (r.get("glosa") or "").strip(): self.fix[h]=r["glosa"].strip()
                if h and (r.get("uppslagsform") or "").strip(): self.fixw[h]=nfc(r["uppslagsform"])

    def _tbesg(self,path):
        self.T=collections.defaultdict(list); self.num={}; self.senses=collections.defaultdict(list)
        for l in open(path,encoding="utf-8-sig"):
            p=l.rstrip("\n").split("\t")
            if len(p)<8 or not re.match(r'^G\d+[A-Za-z]?$',p[0]): continue
            n=int(re.sub(r'\D','',p[0])); L=nfc(p[3]); g=p[6].strip()
            e=(n,g)
            if e not in self.T[L]: self.T[L].append(e)
            self.num.setdefault(n,e)
            if ':' in g:
                s=g.split(':',1)[1].strip()
                if s and s not in self.senses[(L,n)]: self.senses[(L,n)].append(s)
        self.Ts=collections.defaultdict(list)
        for L,v in self.T.items(): self.Ts[strip(L)]+=[(L,)+x for x in v]

    def _macula(self,path):
        self.strong=collections.defaultdict(collections.Counter); hdr=None
        for l in open(path,encoding="utf8"):
            p=l.rstrip("\n").split("\t")
            if hdr is None: hdr={k:i for i,k in enumerate(p)}; continue
            s=p[hdr["strong"]]
            if s.isdigit(): self.strong[nfc(p[hdr["lemma"]])][int(s)]+=1

    def _morph(self,lines):
        self.gender=collections.defaultdict(collections.Counter)
        self.gen=collections.defaultdict(lambda:collections.defaultdict(collections.Counter))
        for p in lines:
            if p[1] not in ('N-','A-') or len(p[2])<7: continue
            L=nfc(p[6]); c=p[2]
            if p[1]=='N-' and c[6] in 'MFN': self.gender[L][c[6]]+=1
            if c[4]=='G': self.gen[L][c[5]][nfc(p[5])]+=1

    def _entry(self,L,h):
        """(Strongnummer, glosa, lemma i TBESG) för ett uppslagsord."""
        for k in (h,L):
            if k in self.T: return min(self.T[k],key=lambda e:(e[0]>=5625,e[0]))+(k,)
        for k in (h,L):
            if self.strong.get(k):
                n=self.strong[k].most_common(1)[0][0]
                if n in self.num:
                    for TL,v in self.T.items():
                        if self.num[n] in v: return self.num[n]+(TL,)
        c=self.Ts.get(strip(L),[])
        if c:
            TL,n,g=min(c,key=lambda e:(e[1]>=5625,e[1])); return (n,g,TL)
        return None

    def glosa(self,L,h,t):
        """Glosa i appens format, eller '' om ingen finns."""
        if h in self.fix: return self.fix[h]
        e=self._entry(L,h)
        if not e: return ''
        n,g,TL=e
        main=_clean(g,t)
        extra=[s for s in self.senses.get((TL,n),[]) if s.lower() not in main.lower()]
        return main+(', '+', '.join(extra) if extra else '')

    def uppslagsord(self,L,h,t):
        """Verb: lemmat. Substantiv: 'λόγος, -ου, ὁ' med genitiv och genus ur NT."""
        if t!='N': return h
        if h in self.fixw: return self.fixw[h]
        g=self.gender.get(L); a=strip(h)
        if a.endswith('ον') or a.endswith('μα'): G='N'
        elif g: G=g.most_common(1)[0][0]
        else: G='F' if a[-1] in 'αη' else 'M'
        art={'M':'ὁ','F':'ἡ','N':'τό'}[G]
        sg=self.gen[L].get('S')
        gen=_suffix(h,sg.most_common(1)[0][0]) if sg else _rule(h,G)
        return f"{h}, {gen or '–'}, {art}"

def _rule(h,G):
    """Genitiv singular för vanliga ändelser när formen inte finns i NT."""
    a=strip(h); acc=h[-2:]!=a[-2:] and h[-2] in 'όήάύ' or h[-1] in 'όήάῆᾶ'
    if a.endswith('ος'): return '-ους' if G=='N' else ('-οῦ' if h.endswith('ός') else '-ου')
    if a.endswith('ον'): return '-οῦ' if h.endswith('όν') else '-ου'
    if a.endswith('η'): return '-ῆς' if h[-1] in 'ήῆ' else '-ης'
    if a.endswith('α') and G=='F': return ('-ᾶς' if h[-1]=='ά' else '-ας') if a[-2] in 'ειρ' else '-ης'
    if a.endswith('ης') and G=='M': return '-οῦ' if h.endswith('ής') else '-ου'
    if a.endswith('ας') and G=='M': return '-ᾶ' if h.endswith('ᾶς') else '-ου'
    if a.endswith('ευς'): return '-έως'
    if a.endswith('ις') and G=='F': return '-εως'
    if a.endswith('οτης') or a.endswith('υτης'): return '-ητος'
    if a.endswith('μα'): return '-ατος'
    return ''

VOW=set('αεηιουω')
DIPH={'αι','ει','οι','υι','αυ','ευ','ηυ','ου'}
def _suffix(lemma,gen):
    """λόγος+λόγου → -ου, πνεῦμα+πνεύματος → -ατος, Σίμων+Σίμωνος → -ωνος, ἀνήρ+ἀνδρός → ἀνδρός."""
    a,b=strip(lemma),strip(gen)
    if a==b: return gen
    p=0
    while p<min(len(a),len(b)) and a[p]==b[p]: p+=1
    r,s=a[p:],b[p:]
    if p==0 or p<len(a)-2: return gen
    if r=='ς' and s and s[0] not in VOW:               # ἐλπί|δος, χάρι|τος, μάρτυ|ρος
        p-=1
        if p>0 and b[p-1:p+1] in DIPH: p-=1
        return '-'+gen[p:] if p>1 else gen
    if r and s and s[0] not in VOW: return gen         # νύξ/νυκτός, πατήρ/πατρός
    if r and r[0] in VOW:                              # πόλ|ις → -εως, Ζαχαρί|ας → -ου
        if p>0 and a[p-1:p+1] in DIPH: p-=1            # βασιλ|εύς → -έως
    elif b[p-1] in VOW:                                # λόγ|ου, Γαλιλαί|ας, Ἰησ|οῦ
        p-=1
        if p>0 and b[p-1:p+1] in DIPH: p-=1
    else:                                              # Σίμ|ωνος, Καῖσ|αρος
        while p>0 and b[p-1] not in VOW: p-=1
        while p>0 and b[p-1] in VOW: p-=1
    return '-'+gen[p:] if p>1 else gen
