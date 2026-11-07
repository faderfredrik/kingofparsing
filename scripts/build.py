#!/usr/bin/env python3
"""Bygger login/index.html från öppna källor + en kursfil med kapitelindelning.
Användning: python3 scripts/build.py [--kurs kurser/mounce.tsv] [--okrypterad fil.html]

Källor: SBLGNT/MorphGNT (former och parsning), STEPBible TBESG (glosor),
MACULA Greek (Strong's-nummer). Allt laddas ned automatiskt till scripts/.cache/.
Kursfilen (kurser/mounce.tsv) skapas en gång med scripts/exportera_mounce.py och
committas aldrig.

Lösenordet frågas efter vid körning (eller sätts med miljövariabeln KOP_PASSWORD).
Skriv aldrig in lösenordet i någon fil i repot.
Med --okrypterad skrivs appen okrypterad till den angivna filen (för lokal test,
lägg den utanför repot) och login/index.html lämnas orörd."""
import sys,os,io,zipfile,urllib.request,argparse
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
ap=argparse.ArgumentParser()
ap.add_argument("--kurs",default=os.path.join(ROOT,"kurser","mounce.tsv"))
ap.add_argument("--okrypterad")
ARGS=ap.parse_args()
KURS=os.path.abspath(ARGS.kurs)
if not os.path.exists(KURS):
    sys.exit(f"Hittar inte kursfilen {KURS}. Kör först: python3 scripts/exportera_mounce.py")
CACHE=os.path.join(HERE,".cache"); os.makedirs(CACHE,exist_ok=True)
ALL=os.path.join(CACHE,"all.txt")
if not os.path.exists(ALL):
    print("Laddar ned MorphGNT …")
    z=zipfile.ZipFile(io.BytesIO(urllib.request.urlopen("https://codeload.github.com/morphgnt/sblgnt/zip/refs/heads/master").read()))
    with open(ALL,"w",encoding="utf8") as out:
        for n in sorted(z.namelist()):
            if n.endswith("-morphgnt.txt"): out.write(z.read(n).decode("utf8"))
os.chdir(CACHE)
# ---- steg 1: matcha glosor mot NT-former ----
import csv,unicodedata as u,collections,json,re
sys.path.insert(0,HERE)
from lexikon import Lexikon
def nfc(s): return u.normalize('NFC',s.strip())
lines=[l.split() for l in open(ALL,encoding='utf8')]
LEX=Lexikon(CACHE,lines,os.path.join(HERE,"glosor_rattelser.tsv"))
# principalformer: framtagna med greek-inflexion (scripts/generera_principalformer.py) + egna rättelser
PP={}
SLOT={'futurum':0,'aorist':1,'perfekt aktiv':2,'perfekt m/p':3,'aorist passiv':4}
if os.path.exists(os.path.join(HERE,'principalformer.tsv')):
    for r in csv.DictReader(open(os.path.join(HERE,'principalformer.tsv'),encoding='utf8'),delimiter='\t'):
        PP[nfc(r['lemma'])]=[x.strip() for x in r['principalformer'].split(',')]
    rf=os.path.join(HERE,'principalformer_rattelser.tsv')
    if os.path.exists(rf):
        for r in csv.DictReader(open(rf,encoding='utf8'),delimiter='\t'):
            L=nfc(r['lemma'])
            if L in PP and r['form'] in SLOT: PP[L][SLOT[r['form']]]=nfc(r['värde'])
def ppfor(L,t): return ', '.join(PP[L]) if t=='V' and L in PP else ''
# words
words=[];lem2w=collections.defaultdict(list);noglosa=[]
for r in csv.DictReader(open(KURS,encoding='utf8'),delimiter='\t'):
    L,head,t,ch=nfc(r['lemma']),nfc(r['uppslagsord']),r['ordklass'],int(r['kapitel'])
    m=LEX.glosa(L,head,t)
    if not m: noglosa.append(head)
    words.append(dict(ch=ch,t=t,w=LEX.uppslagsord(L,head,t),h=head,m=m,pp=ppfor(L,t),L=L))
    lem2w[L].append(len(words)-1)
# övriga läroböcker: lägg till substantiv och verb som saknas i grundlistan
# Duff och Croy är tillfälligt borttagna: kapitelindelningen är inte komplett och författarna är inte tillfrågade.
# Lägg tillbaka dem här när det är klart:
#   ('duff','Duff','The Elements of New Testament Greek'),('croy','Croy','A Primer of Biblical Greek')
KURSER=[('mounce','Mounce','Basics of Biblical Greek')]
KDIR=os.path.dirname(KURS)
nforms=collections.defaultdict(set)
for p in lines:
    if p[1] in ('N-','V-'): nforms[nfc(p[6])].add(nfc(p[5]))
for bid,_,_ in KURSER[1:]:
    fn=os.path.join(KDIR,bid+'.tsv')
    if not os.path.exists(fn): continue
    for r in csv.DictReader(open(fn,encoding='utf8'),delimiter='\t'):
        L,t=nfc(r['lemma']),r['ordklass']
        if t not in ('N','V') or L in lem2w or len(nforms[L])<2: continue   # oböjliga ord hoppas över
        m=LEX.glosa(L,L,t)
        if not m: noglosa.append(L)
        words.append(dict(ch=99,t=t,w=LEX.uppslagsord(L,L,t),h=L,m=m,pp=ppfor(L,t),L=L))
        lem2w[L].append(len(words)-1)
if noglosa: print('Saknar glosa:',' '.join(noglosa))
print(len(words))
# forms
forms={}  # (form,widx)->dict
verses=collections.defaultdict(list)
for i,p in enumerate(lines):
    verses[p[0]].append(p[3])
# MorphGNT för både det opersonliga δεῖ (”det är nödvändigt”) och δέομαι (”be, bönfalla”) till δέω (”binda”).
# Här flyttas de formerna till rätt ord. δέομαι finns inte i ordlistan, så de formerna hoppas över.
FORMLEMMA={('δέω',f):'δεῖ' for f in ('δεῖ','ἔδει','δεῖν','δέον','δέοντα','δέῃ')}
FORMLEMMA.update({('δέω',f):'δέομαι' for f in ('δεήθητε','ἐδεήθη','ἐδεήθην','δεόμεθα','δεόμενος','ἐδεῖτο')})
vpos=collections.Counter()
order=[]
for p in lines:
    bcv=p[0]; idx=vpos[bcv]; vpos[bcv]+=1
    pos,code=p[1],p[2]; L=nfc(p[6])
    L=FORMLEMMA.get((L,nfc(p[5])),L)
    if L not in lem2w: continue
    cand=lem2w[L]
    if pos=='V-':
        tense,voice,mood=code[1],code[2],code[3]
        if mood=='O': continue
        if mood=='P' and tense=='F': continue
        if mood=='I': pc=tense+voice+mood+code[0]+code[5]
        elif mood in 'SD': pc=tense+voice+mood+code[0]+code[5]
        elif mood=='N': pc=tense+voice+'N'
        else: pc=tense+voice+'P'+code[4]+code[5]+code[6]
        cand=[k for k in cand if words[k]['t']=='V']
        if not cand: continue
        if len(cand)>1:
            dep=[k for k in cand if words[k]['h'].endswith('μαι')]; act=[k for k in cand if not words[k]['h'].endswith('μαι')]
            cand=dep if (voice in 'MP' and dep) else (act or cand)
    else:
        if pos not in ('N-','A-'): continue
        if code[4]=='-' : continue
        pc=code[4]+code[5]+code[6]
        cand=[k for k in cand if words[k]['t']=='N']
        if not cand: continue
    wi=cand[0]
    f=nfc(p[5]).replace('(ν)','ν').replace('(ς)','ς')
    key=(f,wi)
    if key not in forms:
        forms[key]=dict(f=f,w=wi,p=collections.Counter(),n=0,r=(bcv,idx))
    forms[key]['p'][pc]+=1; forms[key]['n']+=1
print(len(forms))
# check words without forms
nof=[w['w'] for k,w in enumerate(words) if not any(fk[1]==k for fk in forms)]
print('noforms',nof)
json.dump(dict(words=words,forms=[dict(f=v['f'],w=v['w'],p=dict(v['p']),n=v['n'],r=v['r']) for v in forms.values()],verses=verses),open('raw.json','w'),ensure_ascii=False)
# ---- steg 2: tvetydigheter och kompakt data ----
import json,re,collections
d=json.load(open('raw.json'))
words=d['words'];forms=d['forms'];verses=d['verses']
used=sorted({f['w'] for f in forms})
remap={o:i for i,o in enumerate(used)}
W=[words[o] for o in used]
def aug_noun(f,codes,word):
    s=set(codes)
    gen=word['w'].split(',')[1].strip()
    for c in list(s):
        C,N,G=c
        if N=='P' and C in 'NV': s|={'N'+N+G,'V'+N+G}
        if G=='N' and C in 'NAV': s|={x+N+G for x in 'NAV'}
        if G=='F' and gen.endswith('ας') and f.endswith('ας') and c in('GSF','APF'): s|={'GSF','APF'}
        if gen.endswith('εως') and f.endswith('εις') and C in 'NA' and N=='P': s|={'NP'+G,'AP'+G,'VP'+G}
    return s
def aug_verb(f,codes,word):
    s=set(codes)
    for c in list(s):
        t,v,m=c[0],c[1],c[2]
        if t in 'PIXY' and v in 'MP':
            for vv in 'MP': s.add(t+vv+c[2:])
    for c in list(s):
        t,v,m=c[0],c[1],c[2]
        if m=='I' and v=='A' and t in 'IA' and re.search('(ον|ουν|ων)$',f):
            if c[3:]=='1S': s.add(c[:3]+'3P')
            if c[3:]=='3P': s.add(c[:3]+'1S')
        if t=='P' and m in 'ID' and c[3:]=='2P' and re.search('(ετε|εῖτε|ᾶτε|οῦτε|εσθε|εῖσθε|ᾶσθε|οῦσθε)$',f) and word['h']!='εἰμί':
            s.add(t+v+('D' if m=='I' else 'I')+'2P')
        if m=='P':
            C,N,G=c[3],c[4],c[5]; b=c[:3]
            if C in 'GD' and G in 'MN': s|={b+C+N+'M',b+C+N+'N'}
            if C in 'NV': s|={b+'N'+N+G,b+'V'+N+G}
            if G=='N' and C in 'NAV': s|={b+x+N+'N' for x in 'NAV'}
            if c[3:]=='ASM' and re.search('(ντα|ότα|ῶτα)$',f): s|={b+'NPN',b+'APN',b+'VPN'}
            if c[3:] in('NPN','APN') and re.search('(ντα|ότα|ῶτα)$',f): s.add(b+'ASM')
            if c[3:]=='ASM' and f.endswith('μενον'): s|={b+'NSN',b+'ASN',b+'VSN'}
            if c[3:] in('NSN','ASN') and f.endswith('μενον'): s.add(b+'ASM')
            if C=='G' and N=='P' and f.endswith('μένων'): s|={b+'GP'+x for x in 'MFN'}
    return s
F=[];refs=set()
for f in forms:
    w=words[f['w']]
    codes=aug_noun(f['f'],f['p'],w) if w['t']=='N' else aug_verb(f['f'],f['p'],w)
    bcv,idx=f['r']; refs.add(bcv)
    F.append([f['f'],remap[f['w']],'|'.join(sorted(codes)),f['n'],bcv+'.'+str(idx)])
V={k:' '.join(verses[k]) for k in sorted(refs)}
MOM={'N-NA':6,'N-GDV':7,'V-PAI':16,'V-PMI':18,'V-F':19,'V-I':21,'V-A':22,'V-AP':24,'V-X':25,'V-PtP':27,'V-PtA':28,'V-PtX':30,'V-S':31,'V-N':32,'V-D':33}
BOOKS=[]
for bid,name,title in KURSER:
    fn=os.path.join(KDIR,bid+'.tsv')
    if not os.path.exists(fn): continue
    if bid=='mounce': ch=[w['ch'] for w in W]
    else:
        bych={}
        for r in csv.DictReader(open(fn,encoding='utf8'),delimiter='\t'): bych.setdefault(nfc(r['lemma']),int(r['kapitel']))
        ch=[bych.get(w['L'],99) for w in W]
    gram=None; gf=os.path.join(KDIR,bid+'-grammatik.tsv')
    if os.path.exists(gf):
        g={MOM[r['moment']]:int(r['kapitel']) for r in csv.DictReader(open(gf,encoding='utf8'),delimiter='\t') if r.get('moment') in MOM and (r.get('kapitel') or '').strip().isdigit()}
        if len(g)==len(MOM): gram=g
        else: print(f'{bid}: grammatiktabellen är inte komplett ({len(g)} av {len(MOM)} moment), nivån väljs manuellt')
    BOOKS.append(dict(id=bid,name=name,title=title,ch=ch,gram=gram))
    print(bid,sum(1 for c in ch if c!=99),'ord med kapitel')
out=dict(words=[[w['ch'],w['t'],w['w'],w['h'],w['m'],w['pp']] for w in W],forms=F,verses=V,books=BOOKS)
s=json.dumps(out,ensure_ascii=False,separators=(',',':'))
open('data.json','w').write(s)
print(len(W),len(F),len(V),len(s.encode())/1e6)

# ---- steg 2b: morfologisk nedbrytning ----
sys.path.insert(0,HERE)
exec(open(os.path.join(HERE,"analyze.py"),encoding="utf8").read(),{"__name__":"__analyze__"})
_d=json.load(open("data.json",encoding="utf8")); _d.update(json.load(open("morphdata.json",encoding="utf8")))
open("data.json","w",encoding="utf8").write(json.dumps(_d,ensure_ascii=False,separators=(",",":")))
s=open(os.path.join(ROOT,"src","app.html"),encoding="utf8").read()
d=open("data.json",encoding="utf8").read().replace("</","<\\/")
app=s.replace("__DATA__",d)
if ARGS.okrypterad:
    open(os.path.abspath(os.path.join(ROOT,ARGS.okrypterad)) if not os.path.isabs(ARGS.okrypterad) else ARGS.okrypterad,"w",encoding="utf8").write(app)
    sys.exit(f"Klart: okrypterad app skriven till {ARGS.okrypterad}. login/index.html är inte ändrad.")
# ---- steg 3: kryptera appen bakom lösenordet ----
import getpass,gzip,base64,hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
pw=os.environ.get("KOP_PASSWORD")
if not pw:
    pw=getpass.getpass("Lösenord för appen: ")
    if pw!=getpass.getpass("Skriv lösenordet igen: "):
        sys.exit("Lösenorden stämmer inte överens. login/index.html har inte ändrats. Kör bygget igen.")
if not pw: sys.exit("Tomt lösenord. login/index.html har inte ändrats.")
ITER=600000; salt=os.urandom(16); iv=os.urandom(12)
key=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=salt,iterations=ITER).derive(pw.encode("utf8"))
ct=AESGCM(key).encrypt(iv,gzip.compress(app.encode("utf8"),9),None)
b=lambda x:base64.b64encode(x).decode()
payload=json.dumps(dict(id=hashlib.sha256(salt).hexdigest()[:12],salt=b(salt),iv=b(iv),iter=ITER,ct=b(ct)))
login=open(os.path.join(ROOT,"src","login.html"),encoding="utf8").read()
os.makedirs(os.path.join(ROOT,"login"),exist_ok=True)
open(os.path.join(ROOT,"login","index.html"),"w",encoding="utf8").write(login.replace("__PAYLOAD__",payload))
print("Klart: login/index.html (krypterad)")
