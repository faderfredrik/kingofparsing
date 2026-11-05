#!/usr/bin/env python3
"""Tar fram principalformer för alla verb i appen med James Taubers greek-inflexion (MIT-licens).

Användning (körs av användaren, eftersom biblioteket hämtas från internet):
    <python med inflexion, greek-accentuation och pyyaml> scripts/generera_principalformer.py <mapp med greek-inflexion>

Läser:  scripts/.cache/raw.json (skapas av build.py) och kurser/mounce.tsv (för jämförelse)
Skriver: scripts/principalformer.tsv           (öppen, committas)
         kurser/principalformer_jamforelse.tsv (privat, innehåller Mounces former)

Formerna är futurum, aorist, perfekt aktiv, perfekt medium/passiv och aorist passiv,
i första person singular indikativ. Ett tempus som inte förekommer i NT blir ”–”."""
import sys,os,json,csv,re,collections,unicodedata as u
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
GI=os.path.abspath(sys.argv[1])
sys.path.insert(0,GI)
from greek_inflexion import GreekInflexion
import yaml
nfc=lambda s:u.normalize('NFC',s.strip())
def plain(x): return ''.join(c for c in u.normalize('NFD',x) if not u.combining(c)).lower()

# --- stamlexikonet: lägg till augmenterade stammar (3+, 6+) som saknas, härledda ur verbets egna former ---
LEX=yaml.safe_load(open(os.path.join(GI,'STEM_DATA','morphgnt_lexicon.yaml'),encoding='utf8'))
def stemval(v): return str(v).split('#')[0].strip()
def augment_rule(stems):
    """Hitta hur verbet augmenteras genom att jämföra ett par X-/X+ (t.ex. 1- och 1+)."""
    for k in ('1','3','6','2'):
        a,b=stems.get(k+'-'),stems.get(k+'+')
        if not a or not b: continue
        a,b=stemval(a).split('/')[0],stemval(b).split('/')[0]
        n=0
        while n<min(len(a),len(b)) and a[-1-n]==b[-1-n]: n+=1
        return a[:len(a)-n],b[:len(b)-n]
    return None
PREFIX=('ανα','αντ','απ','δι','εισ','εκ','εξ','εν','εμ','εγ','επ','κατ','μετ','παρ','περι','προ','συν','συμ','συγ','συλ','υπ')
LONG={'α':'η','ε':'η','ο':'ω'}
def simple_augment(m):
    """ζηλωσ → ἐζηλωσ, ἀτενισ → ἠτενισ, ἐλεγξ → ἠλεγξ (bara osammansatta verb)."""
    d=u.normalize('NFD',m); base=d[0]; rest=d[1:]
    n=0
    while n<len(rest) and u.combining(rest[n]): n+=1
    marks,tail=rest[:n],rest[n:]
    if base.lower() in 'βγδζθκλμνξπστφχψ': return u.normalize('NFC','ἐ'+m)
    if base.lower()=='ρ': return u.normalize('NFC','ἐρρ'+u.normalize('NFC',tail))
    if base.lower() in LONG and not (tail[:1] in ('ι','υ')): return u.normalize('NFC',LONG[base.lower()]+marks+tail)
    return None
added=collections.Counter(); unaug=[]
for L,e in (LEX or {}).items():
    st=(e or {}).get('stems') or {}
    for k in ('3','6'):
        if st.get(k+'-') and not st.get(k+'+'):
            r=augment_rule(st); minus=stemval(st[k+'-'])
            if r and all(m.startswith(r[0]) for m in minus.split('/')):
                st[k+'+']='/'.join(r[1]+m[len(r[0]):] for m in minus.split('/')); added['från egna former']+=1
            elif not any(plain(L).startswith(x) for x in PREFIX):
                aug=[simple_augment(m) for m in minus.split('/')]
                if all(aug): st[k+'+']='/'.join(aug); added['enkel regel']+=1
                else: unaug.append((L,k))
            else: unaug.append((L,k))
patched=os.path.join(HERE,'.cache','morphgnt_lexicon_augment.yaml')
yaml.safe_dump(LEX,open(patched,'w',encoding='utf8'),allow_unicode=True)
gi=GreekInflexion(os.path.join(GI,'stemming.yaml'),patched)

# --- vilka tempus och diateser som förekommer i NT (alla modus) ---
seen=collections.defaultdict(collections.Counter)
for l in open(os.path.join(HERE,'.cache','all.txt'),encoding='utf8'):
    p=l.split()
    if p[1]=='V-': seen[nfc(p[6])][p[2][1]+p[2][2]]+=1

def gen(L,key):
    try: r=gi.generate(L,key)
    except Exception: return []
    return sorted({nfc(re.sub('[\u0304\u0306]','',u.normalize('NFD',x))) for x in r if '{' not in x}) if r else []

def slots(L):
    c=seen.get(L,collections.Counter())
    fut=('FMI.1S','FAI.1S') if c['FM'] and not c['FA'] else ('FAI.1S','FMI.1S')
    aor=('AMI.1S','AAI.1S') if c['AM'] and not c['AA'] else ('AAI.1S','AMI.1S')
    att=[c['FA']+c['FM']>0, c['AA']+c['AM']>0, c['XA']+c['YA']>0, c['XM']+c['XP']+c['YM']+c['YP']>0, c['AP']+c['FP']>0]
    return [fut,aor,('XAI.1S',),('XMI.1S','XPI.1S'),('API.1S','FPI.1S')],att

missing=[]
def pp(L):
    out=[]; S,att=slots(L)
    for i,alts in enumerate(S):
        f=[]
        for k in alts:
            f=gen(L,k)
            if f: break
        if not f and att[i]: missing.append((L,['futurum','aorist','perfekt aktiv','perfekt m/p','aorist passiv'][i]))
        out.append(' or '.join(f) if f else '–')
    return ', '.join(out)

words=json.load(open(os.path.join(HERE,'.cache','raw.json'),encoding='utf8'))['words']
verbs=sorted({nfc(w['L']) for w in words if w['t']=='V'})
res={L:pp(L) for L in verbs}

with open(os.path.join(HERE,'principalformer.tsv'),'w',encoding='utf8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n')
    w.writerow(['lemma','principalformer'])
    for L in verbs: w.writerow([L,res[L]])
print(f"Skrev {len(verbs)} verb till scripts/principalformer.tsv")

# jämförelse med Mounce (privat)
mounce={}
mf=os.path.join(ROOT,'kurser','mounce.tsv')
if os.path.exists(mf):
    for r in csv.DictReader(open(mf,encoding='utf8'),delimiter='\t'):
        if r['ordklass']=='V' and r['principalformer'].strip(): mounce.setdefault(nfc(r['lemma']),r['principalformer'].strip())
st=collections.Counter(); rows=[]
for L in verbs:
    if L not in mounce: st['finns inte hos Mounce']+=1; continue
    m=re.sub(r'^\(.*?\),\s*','',mounce[L]); ms=[x.strip() for x in m.split(',')]
    ours=[x.strip() for x in res[L].split(',')]
    if len(ms)!=5: st['Mounce har annat format']+=1; continue
    for i,(a,b) in enumerate(zip(ours,ms)):
        A=set(a.split(' or ')); Bs={nfc(x) for x in b.split(' or ')}
        if a=='–' and b=='–': k='båda tomma'
        elif A&Bs: k='samma'
        elif a=='–': k='saknas hos oss'
        elif b=='–': k='bara hos oss'
        else: k='olika'
        st[k]+=1
        if k not in ('samma','båda tomma'): rows.append([L,['futurum','aorist','perfekt aktiv','perfekt m/p','aorist passiv'][i],a,b,k])
if mounce:
    with open(os.path.join(ROOT,'kurser','principalformer_jamforelse.tsv'),'w',encoding='utf8',newline='') as f:
        w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['lemma','form','ny','mounce','skillnad']); w.writerows(rows)
print('Jämförelse per form:',dict(st))
print('Augmenterade stammar tillagda:',dict(added),'| kunde inte augmenteras:',len(unaug))
with open(os.path.join(HERE,'.cache','principalformer_saknas.tsv'),'w',encoding='utf8') as f:
    f.write('lemma\tform\n'+''.join(f'{a}\t{b}\n' for a,b in missing))
print('Tempus som finns i NT men inte kunde bildas:',len(missing),'(se scripts/.cache/principalformer_saknas.tsv)')
print('Klart.')
