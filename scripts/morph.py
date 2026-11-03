import json,unicodedata as u,re,collections,itertools
d=json.load(open('data.json'));W=d['words'];F=d['forms']
def plain(s):
    s=u.normalize('NFD',s); s=''.join(c for c in s if not u.combining(c))
    return s.lower().replace('ς','σ').replace('’','').replace("'",'')
V='αεηιουω'
def isv(c): return c in V
LAB='πβφ';VEL='κγχ';DEN='τδθζ'
def strip_sub(s): return s.replace('Ι','')
PREF=[('ανα',),('αντι','αντ'),('απο','απ'),('δια','δι'),('εισ',),('εκ','εξ'),('εν','εμ','εγ'),('επι','επ'),('κατα','κατ'),('μετα','μετ'),('παρα','παρ'),('περι',),('προσ',),('προ',),('συν','συμ','συγ','συλ'),('υπερ',),('υπο','υπ')]
PREFSURF=sorted({p for g in PREF for p in g},key=len,reverse=True)
CONTR={'ε':[('ει','ει'),('ου','ου'),('ηΙ','ηΙ'),('οι','οι'),('ε','ει'),('ο','ου'),('ω','ω'),('η','η')],
       'α':[('ει','αΙ'),('ου','ω'),('ηΙ','αΙ'),('οι','ωΙ'),('ε','α'),('ο','ω'),('ω','ω'),('η','α')],
       'ο':[('ει','οι'),('ου','ου'),('ηΙ','οι'),('οι','οι'),('ε','ου'),('ο','ου'),('ω','ω'),('η','ω')]}
def sub(s): return s.replace('Ι','ͅ')  # for notes: show subscript
def disp(s):
    x=s.replace('Ι','\u0345'); return u.normalize('NFC',x)
# ---------- junction ----------
def join(lt,L,rt,R,ctx):
    """returns list of (string, notes)"""
    n=[]
    if R=='' :
        if lt=='cv' and L=='ο' and ctx.get('len1s'): return [('ω',['Utan personändelse förlängs bindevokalen ο till ω.'])]
        if lt=='stem' and L.endswith('οντ'): return [(L[:-3]+'ων',['ντ kan inte stå sist i ordet: τ faller bort och ο förlängs till ω.'])]
        if lt=='stem' and L and L[-1] in 'τδθ': return [(L[:-1],[f'{L[-1]} kan inte stå sist i ett grekiskt ord och faller bort.'])]
        return [(L,[])]
    if lt=='cv' and L=='ε' and R=='σ' and ctx.get('len2s'): return [('εισ',['Bindevokalen ε förlängs till ει före ς.'])]
    # intervocalic sigma
    if isv(L[-1]) and R[:1]=='σ' and len(R)>1 and isv(R[1]) and rt=='end' and R in('σαι','σο') and (lt=='cv' or (lt=='form' and L.endswith('α'))):
        R=R[1:]; n.append('σ i ändelsen faller bort mellan två vokaler.')
    if lt=='form' and L.endswith('εσ') and isv(R[0]):
        L=L[:-1]; n.append('Likvida verb: σ i εσ faller bort mellan vokaler.')
        for a,b in CONTR['ε']:
            if R.startswith(a): return [(L[:-1]+b+R[len(a):],n+[f'Kontraktion: ε + {disp(a)} → {disp(b)}.'])]
    if ctx.get('noun') and lt=='stem' and L.endswith('εσ') and R and isv(R[0]):
        L=L[:-1]; n.append('σ i stammen faller bort mellan vokaler.')
        for a,b in [('ο','ου'),('α','η'),('ω','ω'),('ι','ει')]:
            if R.startswith(a): return [(L[:-1]+b+R[len(a):],n+[f'Kontraktion: ε + {a} → {b}.'])]
    if ctx.get('noun') and lt=='stem' and L.endswith('εσ') and R.startswith('σ'):
        return [(L[:-1]+R,n+['σ + σ förenklas till ett σ.'])]
    if R.startswith('νσ'):
        R=R[1:]
        if L[-1]=='ο': L=L[:-1]+'ου'; n.append('ν faller bort före σ, och ο förlängs till ου.')
        elif L[-1]=='ε': L=L[:-1]+'ει'; n.append('ν faller bort före σ, och ε förlängs till ει.')
        else: n.append('ν faller bort före σ.')
        return [(L+R,n)]
    # augment / vocalic reduplication
    if lt in('aug','red') and L=='ε' and isv(R[0]):
        what='augmentet' if lt=='aug' else 'reduplikationen'
        out=[]
        for a,b in [('αι','ηΙ'),('οι','ωΙ'),('αυ','ηυ'),('ευ','ηυ'),('ευ','ευ'),('ει','ει'),('α','η'),('ε','η'),('ε','ει'),('ο','ω'),('η','η'),('ω','ω'),('ι','ι'),('υ','υ')]:
            if R.startswith(a):
                if a==b and a=='ευ': note=f'Stammen börjar på ευ, som här inte förlängs, så {what} syns inte.'
                elif a==b: note=f'Stammen börjar redan på lång vokal ({a}), så {what} syns inte.'
                else: note=f'Stammen börjar på vokal, så {what} förlänger den: {sub(a)} → {disp(b)} (temporalt augment).' if lt=='aug' else f'Stammen börjar på vokal, så reduplikationen förlänger den: {a} → {disp(b)}.'
                out.append((b+R[len(a):],n+[note]))
        return out
    if lt=='pre' and rt in('aug','red'):
        P=L
        if P in('απο','δια','επι','κατα','μετα','παρα','υπο','ανα','αντι') : 
            n.append(f'Prepositionens slutvokal faller bort före augmentet ({P} → {P[:-1]}).' if rt=='aug' else f'Prepositionens slutvokal faller bort före reduplikationen.'); P=P[:-1]
        elif P=='εκ': P='εξ'; n.append('ἐκ skrivs ἐξ före vokal.')
        elif P in('συμ','συγ','συλ'): n.append(f'Prepositionen får tillbaka sin grundform συν före augmentet.'); P='συν'
        elif P in('εμ','εγ'): P='εν'; n.append('Prepositionen får tillbaka sin grundform ἐν före augmentet.')
        return [(P+R,n)]
    # vowel contraction (stems) / noun stem vowels
    if lt=='stem' and isv(L[-1]) and isv(R[0]):
        v=L[-1]
        if ctx.get('noun'):
            c=ctx['code']
            if R=='ι' and c[1]=='S' and c[0]=='D':
                if v=='ο': return [(L[:-1]+'ωΙ',n+['ο + ι: vokalen förlängs till ω och ι skrivs under (ῳ).'])]
                if v in 'ηα': return [(L+'Ι',n+[f'{v} + ι: ι skrivs under ({disp(v+"Ι")}).'])]
            if R.startswith('ω') and v in 'οαη': return [(L[:-1]+R,n+[f'Stamvokalen {v} sväljs av ändelsen ων.'])]
            if R=='α' and v=='ο': return [(L[:-1]+R,n+['Stamvokalen ο faller bort före neutrumändelsen α.'])]
            if R=='ου' and v in 'ηα': return [(L[:-1]+R,n+[f'Stamvokalen {v} faller bort före ου.'])]
            return [(L+R,n)]
        if R=='ειν' and ctx.get('inf') and v in 'αο':
            r={'α':'αν','ο':'ουν'}[v]; return [(L[:-1]+r,n+[f'Kontraktion: {v} + ειν → {r}.'])]
        if v in CONTR:
            for a,b in CONTR[v]:
                if R.startswith(a):
                    return [(L[:-1]+b+R[len(a):],n+[f'Kontraktion: {v} + {disp(a)} → {disp(b)}.'])]
        return [(L+R,n)]
    if lt=='cv' and isv(R[0]):
        for a,b,t in [('ε','αι','ηΙ'),('ε','ο','ου'),('η','αι','ηΙ'),('η','ι','ηΙ')]:
            if L==a and R.startswith(b):
                if b=='ι': return [(t+R[len(b):],n+['η + ι: ι skrivs under (ῃ).'])]
                return [(t+R[len(b):],n+[f'{a} + {b} drar ihop sig till {disp(t)}.'])]
    if lt=='form' and L.endswith('α') and R[0]=='ο':
        return [(L[:-1]+'ω'+R[1:],n+['α + ο drar ihop sig till ω.'])]
    # consonant clusters
    c=L[-1]
    if lt=='stem' and not isv(c):
        r0=R[0]
        if r0=='σ':
            if L.endswith('ντ') and len(L)>2 and isv(L[-3]):
                base=L[:-2]; v=base[-1]; lv={'ο':'ου','ε':'ει'}.get(v,v)
                return [(base[:-1]+lv+R,n+[f'ντ faller bort före σ'+(f', och {v} förlängs till {lv}.' if lv!=v else '.')])]
            if c in LAB: return [(L[:-1]+'ψ'+R[1:],n+[f'{c} + σ skrivs ψ.'])]
            if c in VEL: return [(L[:-1]+'ξ'+R[1:],n+[f'{c} + σ skrivs ξ.'])]
            if c in DEN: return [(L[:-1]+R,n+[f'{c} faller bort före σ.'])]
            if c=='ν': return [(L[:-1]+R,n+['ν faller bort före σ.'])]
        if r0=='θ':
            if c in LAB: return [(L[:-1]+'φ'+R,n+[f'{c} + θ blir φθ.'])]
            if c in VEL: return [(L[:-1]+'χ'+R,n+[f'{c} + θ blir χθ.'])]
            if c in DEN: return [(L[:-1]+'σ'+R,n+[f'{c} + θ blir σθ.'])]
        if r0=='μ':
            if c in LAB: return [(L[:-1]+'μ'+R,n+[f'{c} + μ blir μμ.'])]
            if c in VEL: return [(L[:-1]+'γ'+R,n+[f'{c} + μ blir γμ.'])]
            if c in DEN: return [(L[:-1]+'σ'+R,n+[f'{c} + μ blir σμ.'])]
        if r0=='τ':
            if c in LAB: return [(L[:-1]+'π'+R,n+[f'{c} + τ blir πτ.'])]
            if c in VEL: return [(L[:-1]+'κ'+R,n+[f'{c} + τ blir κτ.'])]
            if c in DEN: return [(L[:-1]+'σ'+R,n+[f'{c} + τ blir στ.'])]
        if R.startswith('σθ'):
            if c in LAB: return [(L[:-1]+'φ'+R[1:],n+[f'{c} + σθ blir φθ.'])]
            if c in VEL: return [(L[:-1]+'χ'+R[1:],n+[f'{c} + σθ blir χθ.'])]
            if c in DEN: return [(L[:-1]+R,n+[f'{c} faller bort före σθ.'])]
    return [(L+R,n)]
def realize(morphs,ctx):
    # right-to-left fold
    res=[('',[],None)]
    for t,m in reversed(morphs):
        new=[]
        for R,notes,rt in res:
            if rt is None:
                if t=='end' and m=='':
                    new.append(('',notes,'endEmpty'))
                else: new.append((m,notes,t))
                continue
            if rt=='endEmpty':
                for s,nn in join(t,m,'end','',ctx): new.append((s,notes+nn,t))
                continue
            if m=='': new.append((R,notes,rt)); continue
            for s,nn in join(t,m,rt,R,ctx): new.append((s,notes+nn,t))
        res=new
    return [(r[0],r[1]) for r in res]

# ---------- endings ----------
PA={'1S':('ο',''),'2S':('ε','σ'),'3S':('ε','ι'),'1P':('ο','μεν'),'2P':('ε','τε'),'3P':('ο','νσι')}
PM={'1S':('ο','μαι'),'2S':('ε','σαι'),'3S':('ε','ται'),'1P':('ο','μεθα'),'2P':('ε','σθε'),'3P':('ο','νται')}
SA={'1S':('ο','ν'),'2S':('ε','σ'),'3S':('ε',''),'1P':('ο','μεν'),'2P':('ε','τε'),'3P':('ο','ν')}
SM={'1S':('ο','μην'),'2S':('ε','σο'),'3S':('ε','το'),'1P':('ο','μεθα'),'2P':('ε','σθε'),'3P':('ο','ντο')}
SAa={'1S':'ν','2S':'σ','3S':'','1P':'μεν','2P':'τε','3P':'σαν'}
SUBJ_A={'1S':('ω',''),'2S':('η','σ'),'3S':('η','ι'),'1P':('ω','μεν'),'2P':('η','τε'),'3P':('ω','νσι')}
SUBJ_M={'1S':('ω','μαι'),'2S':('η','σαι'),'3S':('η','ται'),'1P':('ω','μεθα'),'2P':('η','σθε'),'3P':('ω','νται')}
def A1(pn,f='σα'):
    e={'1S':'','2S':'σ','3S':'','1P':'μεν','2P':'τε','3P':'ν'}[pn]
    fm=f[:-1]+'ε' if pn=='3S' else f
    return [('form',fm),('end',e)]
def A1M(pn,f='σα'): return [('form',f),('end',SM[pn][1])]
IMP_A={'2S':('ε',''),'3S':('ε','τω'),'2P':('ε','τε'),'3P':('ε','τωσαν')}
IMP_M={'2S':('ε','σο'),'3S':('ε','σθω'),'2P':('ε','σθε'),'3P':('ε','σθωσαν')}
def templates(code):
    t,v,m=code[0],code[1],code[2]; pn=code[3:5]
    T=[]  # (pre-stem list, post-stem list, ctx)
    mp=v in 'MP'
    if m=='I':
        if t=='P':
            cv,e=(PM if mp else PA)[pn]; T.append(([],[('cv',cv),('end',e)],{'len1s':not mp,'len2s':not mp}))
        elif t=='I':
            cv,e=(SM if mp else SA)[pn]; T.append(([('aug','ε')],[('cv',cv),('end',e)],{}))
        elif t=='F' and v in 'AM':
            cv,e=(PM if v=='M' else PA)[pn]
            for f in ('σ','εσ'): T.append(([],[('form',f),('cv',cv),('end',e)],{'len1s':v=='A','len2s':v=='A','liq':f=='εσ'}))
        elif t=='F' and v=='P':
            cv,e=PM[pn]
            for f in ('θησ','ησ'): T.append(([],[('form',f),('cv',cv),('end',e)],{}))
        elif t=='A' and v=='A':
            T.append(([('aug','ε')],A1(pn),{'a1':1}))
            T.append(([('aug','ε')],A1(pn,'α'),{'liq':1}))
            T.append(([('aug','ε')],A1(pn,'κα'),{'a1':1}))
            cv,e=SA[pn]; T.append(([('aug','ε')],[('cv',cv),('end',e)],{'a2':1}))
        elif t=='A' and v=='M':
            T.append(([('aug','ε')],A1M(pn),{'a1':1})); T.append(([('aug','ε')],A1M(pn,'α'),{'liq':1}))
            cv,e=SM[pn]; T.append(([('aug','ε')],[('cv',cv),('end',e)],{'a2':1}))
        elif t=='A' and v=='P':
            for f in ('θη','η'): T.append(([('aug','ε')],[('form',f),('end',SAa[pn])],{}))
        elif t=='X' and v=='A':
            e={'1S':'','2S':'σ','3S':'','1P':'μεν','2P':'τε','3P':'νσι'}[pn]
            for f in ('κα','α'):
                fm=f[:-1]+'ε' if pn=='3S' else f
                T.append((['RED'],[('form',fm),('end',e)],{}))
                if pn=='3P': T.append((['RED'],[('form',f),('end','ν')],{}))
        elif t=='X':
            T.append((['RED'],[('end',PM[pn][1])],{}))
        elif t=='Y' and v=='A':
            for f in ('κει','ει'): T.append(([('aug','ε'),'RED'],[('form',f),('end',SAa[pn])],{}))
        elif t=='Y':
            T.append(([('aug','ε'),'RED'],[('end',SM[pn][1])],{}))
    elif m=='S':
        if t in 'PA' and v in 'AM':
            cv,e=(SUBJ_M if mp else SUBJ_A)[pn]
            if t=='P': T.append(([],[('cv',cv),('end',e)],{}))
            else:
                T.append(([],[('form','σ'),('cv',cv),('end',e)],{'a1':1}))
                T.append(([],[('cv',cv),('end',e)],{'a2':1}))
        elif t=='P' and v=='P':
            cv,e=SUBJ_M[pn]; T.append(([],[('cv',cv),('end',e)],{}))
        elif t=='A' and v=='P':
            cv,e=SUBJ_A[pn]
            for f in ('θ',''): T.append(([],([('form',f)] if f else [])+[('cv',cv),('end',e)],{}))
    elif m=='N':
        if t=='P' and v=='A': T.append(([],[('end','ειν')],{'inf':1}))
        elif t=='P': T.append(([],[('cv','ε'),('end','σθαι')],{}))
        elif t=='A' and v=='A':
            T.append(([],[('form','σα'),('end','ι')],{'a1':1})); T.append(([],[('form','α'),('end','ι')],{'liq':1}))
            T.append(([],[('end','ειν')],{'a2':1,'inf':1}))
        elif t=='A' and v=='M':
            T.append(([],[('form','σα'),('end','σθαι')],{'a1':1})); T.append(([],[('cv','ε'),('end','σθαι')],{'a2':1}))
        elif t=='A' and v=='P':
            for f in ('θη','η'): T.append(([],[('form',f),('end','ναι')],{}))
        elif t=='X' and v=='A':
            for f in ('κε','ε'): T.append((['RED'],[('form',f),('end','ναι')],{}))
        elif t=='X': T.append((['RED'],[('end','σθαι')],{}))
        elif t=='F' and v=='A': T.append(([],[('form','σ'),('end','ειν')],{}))
    elif m=='D':
        if t=='P':
            cv,e=(IMP_M if mp else IMP_A)[pn]; T.append(([],[('cv',cv),('end',e)],{}))
        elif t=='A' and v=='A':
            if pn=='2S': T.append(([],[('form','σ'),('end','ον')],{'a1':1}))
            else: T.append(([],[('form','σα'),('end',IMP_A[pn][1])],{'a1':1}))
            if pn=='2S': T.append(([],[('end','ον')],{'liq':1}))
            else: T.append(([],[('form','α'),('end',IMP_A[pn][1])],{'liq':1}))
            cv,e=IMP_A[pn]; T.append(([],[('cv',cv),('end',e)],{'a2':1}))
        elif t=='A' and v=='M':
            if pn=='2S': T.append(([],[('form','σα'),('end','ι')],{'a1':1}))
            else: T.append(([],[('form','σα'),('end',IMP_M[pn][1])],{'a1':1}))
            cv,e=IMP_M[pn]; T.append(([],[('cv',cv),('end',e)],{'a2':1}))
        elif t=='A' and v=='P':
            e={'2S':'τι','3S':'τω','2P':'τε','3P':'τωσαν'}[pn]
            for f in ('θη','η'): T.append(([],[('form',f),('end',e if not(f=='η' and pn=='2S') else 'θι')],{}))
    return T
VAR_LAST={'ψ':'πβφ','ξ':'κγχ','σ':'τδθζν','φ':'πβ','χ':'κγ','μ':'πβφ','γ':'κχ','π':'βφ','κ':'γχ'}
VAR_FIRST={'η':['ε','α'],'ω':['ο'],'ει':['ε'],'ηυ':['ευ','αυ']}
def stem_cands(s,ps):
    c=set()
    for i in range(len(s)):
        for j in range(i+1,len(s)+1):
            x=s[i:j]; c.add(x)
            if x[-1] in VAR_LAST:
                for y in VAR_LAST[x[-1]]: c.add(x[:-1]+y)
    for x in list(c):
        for a,bs in VAR_FIRST.items():
            if x.startswith(a):
                for b in bs: c.add(b+x[len(a):])
    c.add(ps)
    if ps and ps[-1] in 'αεο':
        c.add(ps[:-1]+{'α':'η','ε':'η','ο':'ω'}[ps[-1]])
    return c
DEASP={'φ':'π','θ':'τ','χ':'κ'}
def redups(st):
    if not st: return []
    a=st[0]
    if isv(a): return [('red','ε')]
    if a in 'ζξψ' or (len(st)>1 and not isv(st[1]) and not (st[1] in 'λρμν' and a in 'πβφτδθκγχ')): return [('red','ε')]
    r=[('red',DEASP.get(a,a)+'ε')]
    if len(st)>1 and st[1]=='ν': r.append(('red','ε'))
    return r
def cp(a,b):
    k=0
    while k<min(len(a),len(b)) and a[k]==b[k]: k+=1
    return k
def matchsurf(r,s):
    r=strip_sub(r)
    if r==s: return 0
    if s==r+'ν' and r[-1:] in ('ι','ε'): return 1
    return None
def analyze_verb(form,code,lem,ppA,isComp):
    s=plain(form); L=plain(lem)
    if not(L.endswith('ω') or L.endswith('ομαι')) or L.endswith('μι'): return None
    pre=None; base=L
    if isComp: pre=isComp; base=L[len(pre):]
    ps=base[:-1] if base.endswith('ω') else base[:-4]
    ps2=ps
    if ps.endswith('ζ'): ps2=ps[:-1]+('γ' if re.search('ξ|χθ|γμ|κτ',s) else 'δ')
    elif ps.endswith('σσ') or ps.endswith('ττ'): ps2=ps[:-2]+('γ' if 'γμ' in s else 'κ')
    elif ps.endswith('πτ'): ps2=ps[:-1]
    best=None
    if code[2]=='P': return None
    cands=[ps] if code[0] in 'PI' else stem_cands(s,ps)
    for prel,post,ctx in templates(code):
        for st in cands:
            if not st or not any(isv(ch) for ch in st): continue
            if ctx.get('liq') and st[-1] not in 'λμνρ': continue
            if ctx.get('a2') and st.endswith('σ'): continue
            opts=[[]]
            for x in prel:
                if x=='RED': opts=[o+[rr] for o in opts for rr in redups(st)]
                else: opts=[o+[x] for o in opts]
            if code[0]=='Y': opts+=[[y for y in o if y[0]!='aug'] for o in opts]
            for pl in opts:
                morphs=([('pre',pre)] if pre else [])+pl+[('stem',st)]+post
                for r,notes in realize(morphs,dict(ctx,code=code)):
                    mm=matchsurf(r,s)
                    if mm is None: continue
                    if any('syns inte' in x for x in notes) and not isv(ps[0]): continue
                    if mm: notes=notes+['ν på slutet är ett rörligt ny (ν ephelkystikon).']
                    if code[0] not in 'PI' and ps[-1:] in 'αεο' and st==ps[:-1]+{'α':'η','ε':'η','ο':'ω'}[ps[-1]]:
                        notes=[f'Kontraktionsvokalen {ps[-1]} förlängs till {st[-1]} före tempusformen.' if any(t=='form' for t,_ in post) else f'Kontraktionsvokalen {ps[-1]} förlängs till {st[-1]}.']+notes
                    if code[0]=='Y' and not any(t=='aug' for t,_ in pl): notes=['Pluskvamperfekt saknar ofta augment i koine.']+notes
                    sc=2*cp(st,ps2)-abs(len(st)-len(ps2))+(3 if st==ps2 else 0)
                    if any(t=='form' and m in('θη','θησ','κα','κε','κει') for t,m in post): sc+=2
                    sc-=1.5*len(notes)
                    if ppA:
                        if ctx.get('a2') and not ppA.endswith('ον'): sc-=4
                        if (ctx.get('a1') or ctx.get('liq')) and ppA.endswith('ον'): sc-=4
                    if best is None or sc>best[0]: best=(sc,morphs,notes)
    return best
# ---------- nouns ----------
def noun_endings(decl,code,neut,masc1):
    C,N,G=code
    if decl==2:
        if neut: e={'NS':'ν','AS':'ν','VS':'ν','GS':'υ','DS':'ι','NP':'α','AP':'α','VP':'α','GP':'ων','DP':'ισ'}
        else: e={'NS':'σ','GS':'υ','DS':'ι','AS':'ν','VS':'','NP':'ι','GP':'ων','DP':'ισ','AP':'υσ','VP':'ι'}
    elif decl==1:
        e={'NS':'σ' if masc1 else '','GS':'ου' if masc1 else 'σ','DS':'ι','AS':'ν','VS':'','NP':'ι','GP':'ων','DP':'ισ','AP':'σ','VP':'ι'}
    else:
        if neut: e={'NS':'','AS':'','VS':'','GS':'οσ','DS':'ι','NP':'α','AP':'α','VP':'α','GP':'ων','DP':'σι'}
        else: e={'NS':'σ','GS':'οσ','DS':'ι','AS':'α','VS':'','NP':'εσ','GP':'ων','DP':'σι','AP':'ασ','VP':'εσ'}
    r=[e[C+N]]
    if decl==3 and C+N=='AS' and not neut: r.append('ν')
    if decl==3 and C+N=='NS' and not neut: r.append('')
    return r
def analyze_noun(form,code,word,stem3):
    s=plain(form); lem=plain(word[3]); neut=code[2]=='N'
    parts=[p.strip() for p in word[2].split(',')]
    gen=plain(parts[1]).lstrip('-') if len(parts)>2 else ''
    if gen.endswith('ουσ') and lem.endswith('οσ') and neut:
        if code[0] in 'NAV' and code[1]=='S': return None
        stem3=lem[:-2]+'εσ'
        decl=3; stems=[stem3]
    elif gen.endswith('οσ') or gen.endswith('ωσ') and not gen.endswith('εωσ'):
        if gen.endswith('εωσ'): return None
        decl=3; stems=[stem3] if stem3 else []
    elif gen.endswith('εωσ'): return None
    elif (lem.endswith('οσ') or lem.endswith('ον')) and gen.endswith('ου') and not lem.endswith('ησ'):
        decl=2; stems=[lem[:-1]]
        if code[:2]=='VS' and not neut: stems=[lem[:-2]+'ε']
    elif lem[-1] in 'ηα' or (lem[-2:] in('ησ','ασ') and code[2]=='M' and gen.endswith('ου')):
        decl=1; masc=lem[-1]=='σ'; st=lem[:-1] if masc else lem
        if code[1]=='P': stems=[st[:-1]+'α']
        else:
            stems=[st]
            if st[-1]=='α' and code[0] in 'GD': stems.append(st[:-1]+'η')
            if masc and code[0]=='V': stems=[st[:-1]+'α',st]
    else:
        decl=3; stems=[stem3] if stem3 else []
    masc1=decl==1 and lem[-1]=='σ'
    for st in stems:
        for e in noun_endings(decl,code,neut,masc1):
            morphs=[('stem',st),('end',e)]
            for r,notes in realize(morphs,{'noun':1,'code':code}):
                mm=matchsurf(r,s)
                if mm is None: continue
                if mm: notes=notes+['ν på slutet är ett rörligt ny (ν ephelkystikon).']
                if decl==1 and st!=stems[0]: notes=['Efter andra bokstäver än ε, ι och ρ skiftar α till η i genitiv och dativ singular.']+notes
                if decl==2 and code[:2]=='VS' and not neut: notes=['Stamvokalen ο blir ε i vokativ singular.']+notes
                if decl==1 and code[1]=='P' and lem[-1] in 'ησ' and lem.rstrip('σ')[-1]=='η': notes=['I plural slutar stammen på α.']+notes
                return (morphs,notes)
    return None
