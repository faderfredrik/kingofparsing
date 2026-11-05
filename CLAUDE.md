# King of parsing: projektanteckningar för Claude Code

En webbapp för att träna parsning av koine-grekiska substantiv och verb enligt Bill Mounce, *Basics of Biblical Greek*. Ägaren är svensktalande. **Allt användargränssnitt och all kommunikation sker på svenska.** Glosorna och den böjda översättningen är på engelska, eftersom Mounces glosor är engelska.

## Arkitektur

Appen är en enda statisk HTML-fil som publiceras med GitHub Pages. Den har ingen server och inget ramverk, bara vanlig HTML, CSS och JavaScript.

| Fil | Roll |
|---|---|
| `src/app.html` | Själva appen: HTML, CSS och JS. Platshållaren `__DATA__` byts mot data vid bygget. **Här görs nästan alla ändringar.** |
| `src/login.html` | Inloggningssidan. Platshållaren `__PAYLOAD__` byts mot den krypterade appen. |
| `scripts/build.py` | Bygger `index.html` (se nedan). |
| `scripts/lexikon.py` | Den öppna ordbasen: glosor från STEPBible TBESG, Strong’s-nummer från MACULA Greek och substantivens uppslagsform (genitiv och genus) ur MorphGNT. |
| `scripts/glosor_rattelser.tsv` | Projektets egna rättelser av glosor och uppslagsformer. Den här filen är öppen och committas. |
| `scripts/exportera_mounce.py` | Engångsskript som skriver Mounces kapitelindelning från `glosor.sqlite` till `kurser/mounce.tsv`. |
| `kurser/` | Kursfiler med läroböckernas kapitelindelning (`mounce.tsv`, `duff.tsv`, `croy.tsv`) och grammatikordning (`<bok>-grammatik.tsv`). **Committas aldrig.** |
| `scripts/morph.py`, `scripts/analyze.py` | Motorn för morfologisk nedbrytning (sprängskissen). |
| `index.html` | Byggd och krypterad. **Redigera aldrig den här filen för hand.** |

### Bygget

```
python3 scripts/build.py
```

Med `--okrypterad <fil>` skrivs appen okrypterad till en fil utanför repot för lokal test, och `index.html` lämnas orörd. Med `--kurs <fil>` väljs en annan kursfil än `kurser/mounce.tsv`.

Bygget gör följande steg i tur och ordning:

1. Laddar ned MorphGNT (SBLGNT med parsning), STEPBible TBESG och MACULA Greek till `scripts/.cache/`.
2. Läser ordlistan och kapitlen ur kursfilen `kurser/mounce.tsv` och hämtar glosor och uppslagsformer ur den öppna ordbasen (`lexikon.py`).
3. Lägger till regler för tvetydiga former och packar datan kompakt.
4. Kör morfologianalysen och lägger in den i datan.
5. Infogar datan i `src/app.html`.
6. Krypterar appen med AES-GCM. Nyckeln tas fram med PBKDF2-SHA256 i 600 000 iterationer.
7. Lägger in det krypterade paketet i `src/login.html` och skriver resultatet till `index.html`.

Glosorna kommer från öppna källor med CC BY-licens. TBESG-glosan putsas till appens format (”to write”, ”spirit, breath”) och kan ersättas via `glosor_rattelser.tsv`. Kursfilen har kolumnerna `lemma`, `uppslagsord`, `ordklass`, `kapitel` och `principalformer`. Principalformerna kommer tills vidare från Mounce och ska ersättas med fritt framtagna former.

`scripts/glosor.sqlite` (Mounce) behövs bara för att skapa `kurser/mounce.tsv` med `exportera_mounce.py`.

Bygget kräver `pip install cryptography`. Det tar några minuter, och analyssteget är det som tar längst tid.

### Regler som aldrig får brytas

- **Lösenordet får aldrig skrivas in i någon fil, något commit-meddelande eller någon kod.** Skriptet frågar efter det med `getpass`, eller läser miljövariabeln `KOP_PASSWORD` som användaren själv sätter i terminalen. Fråga användaren i stället för att gissa.
- **`glosor.sqlite` och `kurser/` får aldrig committas.** Läroböckernas material är upphovsrättsskyddat. Repot är publikt, och därför finns kapitelindelningen bara i krypterad form i `index.html`. `.gitignore` utesluter `*.sqlite`, `kurser/` och `scripts/.cache/`.
- Källhänvisningarna längst ned på startsidan krävs av CC BY-licenserna och får inte tas bort.
- Bygg alltid om `index.html` efter en ändring i `src/` och committa båda filerna tillsammans.

### Testa lokalt

`crypto.subtle` kräver en säker kontext, så appen fungerar inte via `file://`. Kör i stället `python3 -m http.server 8000` i repots rotmapp och öppna `http://localhost:8000`. Vill du testa appen okrypterad kan du skriva ut den sammanfogade appfilen till en temporär fil utanför repot.

## Data i appen (`D` i JS)

- `words`: `[kapitel, typ 'N'|'V', fullt uppslagsord, grundform, betydelse, principalformer]`. Kapitel 99 betyder ”Övriga”, alltså glosor utanför bokens kapitel.
- `forms`: `[form, ordindex, godkända parsningskoder skilda med '|', antal förekomster i NT, exempelreferens 'bcv.ordindex']`.
- `verses`: versers text, nycklade på bcv.
- `an` och `fa`: nedbrytningar och kopplingen form → kod → nedbrytning.

Parsningskoderna skrivs så här:

| Ordklass | Kod |
|---|---|
| Substantiv | kasus + numerus + genus, t.ex. `GSF` |
| Finita verb | tempus + diates + modus + person + numerus, t.ex. `AAI3S` |
| Infinitiv | tempus + diates + `N`, t.ex. `PAN` |
| Particip | tempus + diates + `P` + kasus + numerus + genus, t.ex. `PAPNSM` |

Bokstäverna betyder:

- **Tempus:** P presens, I imperfekt, F futurum, A aorist, X perfekt, Y pluskvamperfekt.
- **Diates:** A aktiv, M medium, P passiv.
- **Modus:** I indikativ, S konjunktiv, D imperativ, N infinitiv, P particip.

Tvetydiga former får alla korrekta parsningar som godkända svar. Medium och passiv räknas som samma sak i presens, imperfekt, perfekt och pluskvamperfekt, och neutrum har samma form i nominativ, ackusativ och vokativ. Reglerna finns i `aug_noun` och `aug_verb` i `build.py`.

## Funktioner och regler

- **Lärobok väljs överst** (`S.book`, Mounce, Duff eller Croy). Varje bok har ett kapitel per ord (`D.books[].ch`, 99 = ”Övriga”) och en grammatiktabell (`gram`) som anger i vilket kapitel varje grammatiskt moment introduceras. Momenten har Mounces kapitelnummer som intern nyckel (`MOMENTS` i appen, `MOM` i `build.py`). Grammatiktabellerna ligger i `kurser/<bok>-grammatik.tsv`. Saknas ett moment där väljs nivån manuellt bland momenten i stället. Croys tabell är ifylld från bokens innehållsförteckning. Duffs bygger på kapitelrubrikerna och ordlistan, och några rader är tolkningar (se kolumnen `källa`). Former utanför indikativ (particip, infinitiv, konjunktiv, imperativ) kräver både sitt modusmoment och sitt tempusmoment (`needs` och `tenseKey` i appen), eftersom Croy tar upp infinitiv redan i lektion 2. Inställningarna sparas per bok i `S.by`.
- Ord från Duff och Croy som inte finns i Mounces lista läggs till automatiskt, utom oböjliga ord.
- **Kunskapsnivå och glosor väljs separat.** `S.level`, där 0 betyder automatisk, styr grammatiken. Kapitelvalet styr glosorna. Kapitlet som motsvarar nivån får en guldfärgad outline i kapitelrutnätet.
- **Grammatik per kapitel i Mounce** (`verbCh` och `nounCh` ger momentets nyckel):

  | Kapitel | Grammatik som tillkommer |
  |---|---|
  | 6 | Nominativ och ackusativ |
  | 7 | Genitiv, dativ och vokativ |
  | 16 | Presens aktiv indikativ |
  | 18 | Presens medium/passiv |
  | 19 | Futurum aktiv/medium |
  | 21 | Imperfekt |
  | 22 | Aorist aktiv/medium |
  | 24 | Aorist och futurum passiv |
  | 25 | Perfekt och pluskvamperfekt |
  | 27 | Presens particip |
  | 28 | Aorist particip |
  | 30 | Perfekt particip |
  | 31 | Konjunktiv |
  | 32 | Infinitiv |
  | 33 | Imperativ |

- **Sprängskissen** visas efter ”Kontrollera svar”. Ordet delas upp i Prefix, Augment, Reduplikation, Stam, Tempusform, Bindevokal och Ändelse, eller Kasusändelse för substantiv, med en klammer och etikett över varje del. Under delarna förklaras ljudförändringarna på svenska.
  - Motorn i `morph.py` tar fram de bakomliggande delarna och bygger ihop dem igen med ljudregler. **En nedbrytning sparas bara om den återskapar den verkliga NT-formen exakt.** Den principen ska behållas.
  - Particip, μι-verb, εἰμί, attisk reduplikation och substantiv av typen πόλις saknar ännu nedbrytning.
- **Böjd översättning** (`inflTr` i `src/app.html`) bygger på ordets första glosa och engelska böjningsregler. Deponensverb översätts aktivt.
  - Medium av icke-deponensverb i presens, imperfekt, perfekt och pluskvamperfekt översätts som passiv.
  - För substantiv står ”(subjekt)” eller ”(objekt)” på svenska efter den engelska översättningen.
- **Lagring:** `localStorage` används för `kop-settings`, `kop-life` och `kop-key-<id>`, där den sista sparar inloggningen för ”kom ihåg mig”. Läsningar och skrivningar är alltid inslagna i try/catch.
- **Tangentbord:** Enter kontrollerar svaret och går sedan vidare till nästa ord.

## Design

- **Platt design:** inga skuggor, inga gradienter och inga ramar på kort. Ytorna har solida färger. Valda knappar fylls med lapisblått, rätt svar visas i grönt och fel i rött.
- **Färgtema:** lapisblått och guld, inspirerat av bysantinsk ikonkonst. Alla färger är CSS-variabler på `:root` och har mörka varianter under `prefers-color-scheme: dark`.
- **Typsnitt:**
  - Gentium Book Plus för grekisk text.
  - Figtree för gränssnittet. Gentium ligger som fallback, så att grekiska tecken i gränssnittstext också renderas med Gentium.
  - Cinzel för logotypen ”King of Parsing”, där ”of” sätts mindre.
- **Logotyp:** en platt guldfärgad korintisk hjälm sedd framifrån, gjord i inline-SVG.
- **Typografi:** svensk text använder citattecknet ” och apostrofen ’.
- **Etiketter:** sentence case, aldrig versaler. Morfemen i sprängskissen skrivs utan accenter, som i Mounce.
- **Mobil:** rutorna ligger i en enda kolumn, och safe-area-insets respekteras.

## Källor

- Glosor: STEPBible-Data (TBESG), Tyndale House Cambridge och STEPBible.org, CC BY 4.0. Bygger på Abbott-Smith och Middle Liddell.
- Strong’s-nummer: MACULA Greek, Biblica, CC BY 4.0.
- Kapitelindelning: Mounce, *Basics of Biblical Greek* (privat kursfil).
- Text: SBL Greek New Testament.
- Morfologi: MorphGNT (github.com/morphgnt/sblgnt).
