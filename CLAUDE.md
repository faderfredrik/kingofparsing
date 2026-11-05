# King of parsing: projektanteckningar för Claude Code

En webbapp för att träna parsning av koine-grekiska substantiv och verb enligt Bill Mounce, *Basics of Biblical Greek*. Ägaren är svensktalande. **Allt användargränssnitt och all kommunikation sker på svenska.** Glosorna och den böjda översättningen är på engelska, eftersom Mounces glosor är engelska.

## Arkitektur

Appen är en enda statisk HTML-fil som publiceras med GitHub Pages. Den har ingen server och inget ramverk, bara vanlig HTML, CSS och JavaScript.

| Fil | Roll |
|---|---|
| `src/app.html` | Själva appen: HTML, CSS och JS. Platshållaren `__DATA__` byts mot data vid bygget. **Här görs nästan alla ändringar.** |
| `src/login.html` | Inloggningssidan. Platshållaren `__PAYLOAD__` byts mot den krypterade appen. |
| `scripts/build.py` | Bygger `index.html` (se nedan). |
| `scripts/morph.py`, `scripts/analyze.py` | Motorn för morfologisk nedbrytning (sprängskissen). |
| `index.html` | Byggd och krypterad. **Redigera aldrig den här filen för hand.** |

### Bygget

```
python3 scripts/build.py
```

Bygget gör följande steg i tur och ordning:

1. Laddar ned MorphGNT (SBLGNT med parsning) till `scripts/.cache/`.
2. Matchar Mounces glosor ur `scripts/glosor.sqlite` mot de lemman som förekommer i NT.
3. Lägger till regler för tvetydiga former och packar datan kompakt.
4. Kör morfologianalysen och lägger in den i datan.
5. Infogar datan i `src/app.html`.
6. Krypterar appen med AES-GCM. Nyckeln tas fram med PBKDF2-SHA256 i 600 000 iterationer.
7. Lägger in det krypterade paketet i `src/login.html` och skriver resultatet till `index.html`.

Glosorna ligger i `scripts/glosor.sqlite`, som har tabellen `glosor` med kolumnerna `id`, `kapitel`, `typ` (N, V eller U), `ord`, `betydelse`, `principalformer` och `frekvens`.

Bygget kräver `pip install cryptography`. Det tar några minuter, och analyssteget är det som tar längst tid.

### Regler som aldrig får brytas

- **Lösenordet får aldrig skrivas in i någon fil, något commit-meddelande eller någon kod.** Skriptet frågar efter det med `getpass`, eller läser miljövariabeln `KOP_PASSWORD` som användaren själv sätter i terminalen. Fråga användaren i stället för att gissa.
- **`glosor.sqlite` får aldrig committas.** Mounces material är upphovsrättsskyddat. Repot är publikt, och därför finns glosorna bara i krypterad form i `index.html`. `.gitignore` utesluter `*.sqlite` och `scripts/.cache/`.
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

- **Kunskapsnivå och glosor väljs separat.** `S.level`, där 0 betyder automatisk, styr grammatiken. Kapitelvalet styr glosorna. Kapitlet som motsvarar nivån får en guldfärgad outline i kapitelrutnätet.
- **Grammatik per kapitel** (`verbCh` och `nounCh`):

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
- **Böjd översättning** (`inflTr` i `src/app.html`) bygger på Mounces första glosa och engelska böjningsregler. Deponensverb översätts aktivt.
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

- Glosor: Mounce, *Basics of Biblical Greek*.
- Text: SBL Greek New Testament.
- Morfologi: MorphGNT (github.com/morphgnt/sblgnt).
