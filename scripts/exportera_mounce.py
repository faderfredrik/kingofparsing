#!/usr/bin/env python3
"""Engångsskript: skriver Mounces kapitelindelning från glosor.sqlite till kurser/mounce.tsv.
Användning: python3 scripts/exportera_mounce.py [sökväg/till/glosor.sqlite]

Kursfilen innehåller bara uppslagsord, ordklass, kapitel och (tills vidare) principalformer,
inga glosor. Mappen kurser/ committas aldrig."""
import sys,os,re,csv,sqlite3,unicodedata as u
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
DB=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else os.path.join(HERE,"glosor.sqlite")
OUT=os.path.join(ROOT,"kurser","mounce.tsv"); os.makedirs(os.path.dirname(OUT),exist_ok=True)
def nfc(s): return u.normalize('NFC',s.strip())
alias={'ἄρχομαι':'ἄρχω','πορεύω':'πορεύομαι','κοιμάω':'κοιμάομαι','κολλάω':'κολλάομαι','προσκαλέω':'προσκαλέομαι','προσλαμβάνω':'προσλαμβάνομαι','σέβω':'σέβομαι','ἐκπλήσσω':'ἐκπλήσσομαι','ἐλεέω':'ἐλεάω','ἐντέλλω':'ἐντέλλομαι','Ᾰδης':'ᾅδης','σατανᾶς':'Σατανᾶς','ἱερόν':'ἱερός','ἀφίστημι':'ἀφίσταμαι','ἔξεστιν':'ἔξεστι(ν)'}
# Ord som står som U (övrigt) i glosor.sqlite men egentligen är verb
TYPFIX={'ἔξεστιν':'V','ἐξομολογέω':'V'}
rows=sqlite3.connect(DB).execute("select kapitel,typ,ord,principalformer from glosor where typ in ('N','V','U') order by kapitel,id").fetchall()
n=0
with open(OUT,"w",encoding="utf8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n")
    w.writerow(["lemma","uppslagsord","ordklass","kapitel","principalformer"])
    for ch,t,word,pp in rows:
        word=re.sub(r'\s+',' ',nfc(word)); head=nfc(word.split(',')[0])
        t=TYPFIX.get(head,t)
        if t=='U':
            if word.count(',')<2 or head in ('ἐμαυτοῦ','χρυσοῦς'): continue
            t='N'
        if t=='N' and word.count(',')<2: continue
        w.writerow([alias.get(head,head),head,t,ch,(pp or '').strip()]); n+=1
print(f"Skrev {n} ord till {OUT}")
# Mounces grammatikordning: i vilket kapitel varje moment introduceras
MOMENT=[('N-NA','nominativ och ackusativ',6),('N-GDV','genitiv, dativ och vokativ',7),('V-PAI','presens aktiv indikativ',16),
        ('V-PMI','presens medium/passiv indikativ',18),('V-F','futurum aktiv/medium indikativ',19),('V-I','imperfekt indikativ',21),
        ('V-A','aorist aktiv/medium indikativ',22),('V-AP','aorist och futurum passiv',24),('V-X','perfekt och pluskvamperfekt indikativ',25),
        ('V-PtP','presens particip',27),('V-PtA','aorist particip',28),('V-PtX','perfekt particip',30),
        ('V-S','konjunktiv',31),('V-N','infinitiv',32),('V-D','imperativ',33)]
G=os.path.join(ROOT,"kurser","mounce-grammatik.tsv")
with open(G,"w",encoding="utf8",newline="") as f:
    w=csv.writer(f,delimiter="\t",lineterminator="\n"); w.writerow(["moment","beskrivning","kapitel"])
    for m,d,c in MOMENT: w.writerow([m,d,c])
print("Skrev",G)
