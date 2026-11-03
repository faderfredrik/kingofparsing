#!/usr/bin/env python3
"""Bygger index.html från FlashWorks.sqlite + MorphGNT (SBLGNT).
Användning: python3 scripts/build.py sökväg/till/FlashWorks.sqlite
Lösenordet frågas efter vid körning (eller sätts med miljövariabeln KOP_PASSWORD).
Skriv aldrig in lösenordet i någon fil i repot.
Skriptet laddar ned MorphGNT automatiskt till scripts/.cache/."""
import sys,os,io,zipfile,urllib.request
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
DB=sys.argv[1] if len(sys.argv)>1 else os.path.join(HERE,"FlashWorks.sqlite")
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
import sqlite3,unicodedata as u,collections,json,re
def nfc(s): return u.normalize('NFC',s.strip())
def strip(s): return ''.join(c for c in u.normalize('NFD',s) if not u.combining(c)).lower()
alias={'ἄρχομαι':'ἄρχω','πορεύω':'πορεύομαι','κοιμάω':'κοιμάομαι','κολλάω':'κολλάομαι','προσκαλέω':'προσκαλέομαι','προσλαμβάνω':'προσλαμβάνομαι','σέβω':'σέβομαι','ἐκπλήσσω':'ἐκπλήσσομαι','ἐλεέω':'ἐλεάω','ἐντέλλω':'ἐντέλλομαι','Ᾰδης':'ᾅδης','σατανᾶς':'Σατανᾶς','ἱερόν':'ἱερός','ἀφίστημι':'ἀφίσταμαι'}
c=sqlite3.connect(DB)
rows=c.execute("select dbChapter,dbType,dbWord,dbMeaning,dbPrincipalParts,dbFrequency,dbSequence from flash where dbType in ('N','V','U') order by dbChapter,dbSequence").fetchall()
lines=[l.split() for l in open(ALL,encoding='utf8')]
# words
words=[];lem2w=collections.defaultdict(list)
for ch,t,w,m,pp,fr,seq in rows:
    w=re.sub(r'\s+',' ',nfc(w)); head=nfc(w.split(',')[0])
    if t=='U':
        if w.count(',')<2 or head in ('ἐμαυτοῦ','χρυσοῦς'): continue
        t='N'
    if t=='N' and w.count(',')<2: continue
    L=alias.get(head,head)
    m=re.sub(r'<br\s*/?>','; ',m or '').strip(); m=re.sub(r'\s+',' ',m)
    pp=(pp or '').strip()
    words.append(dict(ch=ch,t=t,w=w,h=head,m=m,pp=pp,fr=fr,L=L))
    lem2w[L].append(len(words)-1)
print(len(words))
# forms
forms={}  # (form,widx)->dict
verses=collections.defaultdict(list)
for i,p in enumerate(lines):
    verses[p[0]].append(p[3])
vpos=collections.Counter()
order=[]
for p in lines:
    bcv=p[0]; idx=vpos[bcv]; vpos[bcv]+=1
    pos,code=p[1],p[2]; L=nfc(p[6])
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
out=dict(words=[[w['ch'],w['t'],w['w'],w['h'],w['m'],w['pp']] for w in W],forms=F,verses=V)
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
# ---- steg 3: kryptera appen bakom lösenordet ----
import getpass,gzip,base64,hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
pw=os.environ.get("KOP_PASSWORD") or getpass.getpass("Lösenord för appen: ")
ITER=600000; salt=os.urandom(16); iv=os.urandom(12)
key=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=salt,iterations=ITER).derive(pw.encode("utf8"))
ct=AESGCM(key).encrypt(iv,gzip.compress(app.encode("utf8"),9),None)
b=lambda x:base64.b64encode(x).decode()
payload=json.dumps(dict(id=hashlib.sha256(salt).hexdigest()[:12],salt=b(salt),iv=b(iv),iter=ITER,ct=b(ct)))
login=open(os.path.join(ROOT,"src","login.html"),encoding="utf8").read()
open(os.path.join(ROOT,"index.html"),"w",encoding="utf8").write(login.replace("__PAYLOAD__",payload))
print("Klart: index.html (krypterad)")
