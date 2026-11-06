# Morfologisk nedbrytning: genererar och verifierar morfem mot de verkliga formerna
from morph import *
import random,sys
# Mounce aorist principal part (plain)
def ppA(word):
    pp=word[5]; parts=[p.strip() for p in re.sub(r'\(.*?\)','',pp).split(',')]
    parts=[p for p in parts if p]
    return plain(parts[1]) if len(parts)>1 and parts[1] not in('–','-') else ''
byw=collections.defaultdict(list)
for f in F: byw[f[1]].append(f)
comp={}
for wi,w in enumerate(W):
    if w[1]!='V': continue
    L=plain(w[3])
    cands=[p for p in PREFSURF if L.startswith(p) and len(L)-len(p)>=3]
    if not cands: continue
    aug=[f for f in byw[wi] if any(c[0] in 'IAY' and c[2]=='I' for c in f[2].split('|'))]
    best=None
    for cand in cands:
        yes=0
        for f in aug[:12]:
            c=[c for c in f[2].split('|') if c[0] in 'IAY' and c[2]=='I'][0]
            if analyze_verb(f[0],c,w[3],ppA(w),cand): yes+=1
        if best is None or yes>best[1]: best=(cand,yes)
    no=0
    for f in aug[:12]:
        c=[c for c in f[2].split('|') if c[0] in 'IAY' and c[2]=='I'][0]
        if analyze_verb(f[0],c,w[3],ppA(w),None): no+=1
    cand,yes=best
    if yes>=no and (yes>0 or cand not in('εν','εμ','εγ','συμ','συγ','συλ')): comp[wi]=cand
# 3rd decl stems
stem3={}
for wi,w in enumerate(W):
    if w[1]!='N': continue
    c=collections.Counter()
    for f in byw[wi]:
        s=plain(f[0])
        for code in f[2].split('|'):
            if code[:2]=='GS' and s.endswith('οσ'): c[s[:-2]]+=3
            if code[:2]=='DS' and s.endswith('ι'): c[s[:-1]]+=1
            if code[:2]=='GP' and s.endswith('ων'): c[s[:-2]]+=1
            if code[:2] in('NP','VP') and s.endswith('εσ'): c[s[:-2]]+=1
            if code[:2]=='AP' and s.endswith('ασ'): c[s[:-2]]+=1
            if code[:2]=='AS' and s.endswith('α') and code[2]!='N': c[s[:-1]]+=1
    if any(plain(f[0]).endswith('εωσ') for f in byw[wi]): continue
    if c: stem3[wi]=c.most_common(1)[0][0]
A={};stat=collections.Counter()
for fi,f in enumerate(F):
    w=W[f[1]]
    for code in f[2].split('|'):
        if w[1]=='V':
            if code[2]=='P': stat['V-part']+=1; continue
            r=analyze_verb(f[0],code,w[3],ppA(w),comp.get(f[1]))
            if not r and comp.get(f[1]): r=analyze_verb(f[0],code,w[3],ppA(w),None)
            r=(r[1],r[2]) if r else None
        else:
            r=analyze_noun(f[0],code,w,stem3.get(f[1]))
        stat[w[1]+('ok' if r else 'no')]+=1
        if r: A[(fi,code)]=r
print('Nedbrytningar:',dict(stat))
_f=[(f[0],code,W[f[1]][3]) for fi,f in enumerate(F) for code in f[2].split('|') if (fi,code) not in A and code[2]!='P']
random.seed(3)

json.dump({f'{k[0]}|{k[1]}':v for k,v in A.items()},open('analyses.json','w'),ensure_ascii=False)

# compact output
def dispm(ms):
    out=[];last=max(i for i,(t,m) in enumerate(ms)) 
    nz=[i for i,(t,m) in enumerate(ms) if m]
    for i,(t,m) in enumerate(ms):
        x=disp(m)
        if nz and i==nz[-1] and x.endswith('σ'): x=x[:-1]+'ς'
        out.append([t,x])
    return out
# förklaringarna sparas en gång var i NT som [svenska, engelska]; AN pekar på dem med index
from noter_en import engelska
idx={};AN=[];FA={};NT=[];nix={}
def notindex(x):
    if x not in nix: nix[x]=len(NT);NT.append([x,engelska(x)])
    return nix[x]
for (fi,code),(ms,notes) in A.items():
    nn=[];[nn.append(x) for x in notes if x not in nn]
    key=json.dumps([dispm(ms),[notindex(x) for x in nn]],ensure_ascii=False)
    if key not in idx: idx[key]=len(AN);AN.append(json.loads(key))
    FA.setdefault(str(fi),{})[code]=idx[key]
out={'an':AN,'fa':FA,'nt':NT}
json.dump(out,open('morphdata.json','w'),ensure_ascii=False,separators=(',',':'))
print(len(AN),len(NT),'förklaringar',len(json.dumps(out,ensure_ascii=False).encode())/1e6)
