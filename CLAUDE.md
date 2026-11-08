# King of parsing: projektanteckningar för Claude Code

En webbapp för att träna parsning av koine-grekiska substantiv och verb enligt Bill Mounce, *Basics of Biblical Greek*. Ägaren är svensktalande. **All kommunikation sker på svenska.** Användargränssnittet finns på svenska och engelska (se ”Språk” nedan). Glosorna och den böjda översättningen är på engelska, eftersom Mounces glosor är engelska.

## Arkitektur

Appen är en enda statisk HTML-fil som publiceras med GitHub Pages. Den har ingen server och inget ramverk, bara vanlig HTML, CSS och JavaScript.

| Fil | Roll |
|---|---|
| `src/app.html` | Själva appen: HTML, CSS och JS. Platshållaren `__DATA__` byts mot data vid bygget. **Här görs nästan alla ändringar.** |
| `src/login.html` | Inloggningssidan med konton via Supabase (logga in, skapa konto, glömt och nytt lösenord). Platshållaren `__PAYLOAD__` byts mot den krypterade appen. |
| `supabase/schema.sql`, `supabase/mina-sidor.sql` | Databasens tabeller och regler i Supabase. Körs i Supabase → SQL Editor, i den ordningen. Innehåller inga hemligheter. |
| `scripts/build.py` | Bygger `login/index.html` (se nedan). |
| `scripts/lexikon.py` | Den öppna ordbasen: glosor från STEPBible TBESG, Strong’s-nummer från MACULA Greek och substantivens uppslagsform (genitiv och genus) ur MorphGNT. |
| `scripts/principalformer.tsv`, `scripts/principalformer_rattelser.tsv` | Principalformer för alla verb (öppna, committas) och egna rättelser. |
| `scripts/glosor_rattelser.tsv` | Projektets egna rättelser av glosor och uppslagsformer. Den här filen är öppen och committas. |
| `scripts/exportera_mounce.py` | Engångsskript som skriver Mounces kapitelindelning från `glosor.sqlite` till `kurser/mounce.tsv`. |
| `kurser/` | Kursfiler med läroböckernas kapitelindelning (`mounce.tsv`, `duff.tsv`, `croy.tsv`) och grammatikordning (`<bok>-grammatik.tsv`). **Committas aldrig.** |
| `scripts/morph.py`, `scripts/analyze.py` | Motorn för morfologisk nedbrytning (sprängskissen). |
| `scripts/noter_en.py` | Engelska mallar för sprängskissens förklaringar. Bygget stoppas om en förklaring saknar mall. |
| `login/index.html` | Inloggningssidan med den krypterade appen. Den byggs av `build.py`. **Redigera aldrig den här filen för hand.** |
| `index.html`, `img/` | Onepagern för studenter, som ligger på startadressen. Den skrivs för hand på engelska och byggs inte. Alla knappar för ”Get early access” leder till `login/`. Screenshotsen i `img/` är tagna i mörkt läge. |

### Bygget

```
python3 scripts/build.py
```

Med `--okrypterad <fil>` skrivs appen okrypterad till en fil utanför repot för lokal test, och `login/index.html` lämnas orörd. Med `--kurs <fil>` väljs en annan kursfil än `kurser/mounce.tsv`.

Bygget gör följande steg i tur och ordning:

1. Laddar ned MorphGNT (SBLGNT med parsning), STEPBible TBESG och MACULA Greek till `scripts/.cache/`.
2. Läser ordlistan och kapitlen ur kursfilen `kurser/mounce.tsv` och hämtar glosor och uppslagsformer ur den öppna ordbasen (`lexikon.py`).
3. Lägger till regler för tvetydiga former och packar datan kompakt.
4. Kör morfologianalysen och lägger in den i datan.
5. Infogar datan i `src/app.html`.
6. Krypterar appen med AES-GCM. Nyckeln tas fram med PBKDF2-SHA256 i 600 000 iterationer.
7. Lägger in det krypterade paketet i `src/login.html` och skriver resultatet till `login/index.html`.

Glosorna kommer från öppna källor med CC BY-licens. TBESG-glosan putsas till appens format (”to write”, ”spirit, breath”) och kan ersättas via `glosor_rattelser.tsv`. Kursfilen har kolumnerna `lemma`, `uppslagsord`, `ordklass` och `kapitel`. Kolumnen `principalformer` används inte längre.

Principalformerna ligger i `scripts/principalformer.tsv` och tas fram med James Taubers greek-inflexion (MIT) via `scripts/generera_principalformer.py`. Diatesen och vilka tempus som visas styrs av MorphGNT, och ”–” betyder att tempuset inte förekommer i NT. Egna rättelser ligger i `scripts/principalformer_rattelser.tsv`. Generatorn behöver greek-inflexion utcheckat och **körs av användaren själv i terminalen**, eftersom säkerhetsspärren stoppar Claude från att köra kod hämtad från internet. Bygget behöver inte biblioteket.

`scripts/glosor.sqlite` (Mounce) behövs bara för att skapa `kurser/mounce.tsv` med `exportera_mounce.py`.

Bygget kräver `pip install cryptography`. Det tar några minuter, och analyssteget är det som tar längst tid.

### Regler som aldrig får brytas

- **Lösenordet får aldrig skrivas in i någon fil, något commit-meddelande eller någon kod.** Samma lösenord ligger i tabellen `app_secret` i Supabase och läggs in där av användaren själv. Skriptet frågar efter det med `getpass`, eller läser miljövariabeln `KOP_PASSWORD` som användaren själv sätter i terminalen. Fråga användaren i stället för att gissa.
- **`glosor.sqlite` och `kurser/` får aldrig committas.** Läroböckernas material är upphovsrättsskyddat. Repot är publikt, och därför finns kapitelindelningen bara i krypterad form i `login/index.html`. `.gitignore` utesluter `*.sqlite`, `kurser/` och `scripts/.cache/`.
- Källhänvisningarna längst ned på startsidan krävs av CC BY-licenserna och får inte tas bort.
- Bygg alltid om `login/index.html` efter en ändring i `src/` och committa båda filerna tillsammans.

### Konton (Supabase)

Studenterna skapar konto och loggar in på `/login/`. Supabase sköter konton, lösenord och e-post (via Resend från `noreply@kingofparsing.com`). Efter inloggningen hämtar sidan lösenordet till appen ur tabellen `app_secret`, som bara inloggade får läsa, och låser upp appen som förut. Nyckeln sparas i `kop-key-<id>` tills användaren loggar ut. Inloggningssidan lägger `window.KOP` (`email`, `save(rad)`, `signOut()`) åt appen, som sparar varje svar i tabellen `answers` och visar knappen Logga ut. Project URL och publishable key står i `src/login.html`. De är offentliga. Den hemliga nyckeln (secret/service_role) får aldrig hamna i repot. **När lösenordet byts vid bygget måste det också bytas i `app_secret`**, annars kan ingen öppna appen. Duff och Croy är tillfälligt borttagna ur `KURSER` i `build.py`.

**Demokontot** (`demo@kingofparsing.com`) är till för den som vill prova appen utan eget konto, till exempel lektorer. Ägaren skapar det själv i Supabase (Authentication → Users → Add user, bekräftat automatiskt) och delar en länk av formen `https://kingofparsing.com/login/#demo=<lösenord>`. Lösenordet får bara innehålla bokstäver och siffror, och det **får aldrig skrivas in i repot**. Inloggningssidan loggar ut ett eventuellt annat konto, nollställer `kop-settings` (utom språket), `kop-tour` och `kop-life` och loggar in på demokontot, så att varje besök blir en förstagångsupplevelse. I appen är `DEMO` sant: svaren räknas bara i minnet under besöket, ingenting hämtas eller sparas, och Mina sidor visar rutan Demokonto i stället för Min kurs och Konto. Tyck till fungerar. Databasen spärrar kontot med `is_demo()` i `schema.sql` och `mina-sidor.sql`, så att det inte kan spara svar, ändra profilen, läsa kommentarer eller raderas. Att byta lösenordet går inte att spärra i databasen. Länken stängs av genom att lösenordet byts i Supabase.

### Mina sidor, titlar och svagheter

Knappen Mina sidor uppe till höger, bredvid nivån med sin progressbar, öppnar Mina sidor (`renderMe` i `src/app.html`). Appen hämtar användarens svar ur `answers` vid start (`loadAccount`, sparas i `HIST`) och räknar fram allt i webbläsaren:

- **Nivåer** (i koden `TITLES`): 17 nivåer, en per sektion i `SECTIONS` (Bonde … Prins) plus King of Parsing. Nivåerna räknas likadant i båda lägena (`sectionStats`). Mina sidor visar bara nuvarande nivå och nästa, med en lång progressbar, så att en ny nivå blir en överraskning. En sektion är behärskad vid minst 16 rätt av de senaste 20 formerna utan ledtråd (`NEED`, `PASS`). ”Öva mot nästa nivå” hämtar former ur sektionen (`sectionForms`). Högsta nivån sparas i `profiles.title` och förloras aldrig. En popup visas när en ny nivå nås (`titlePopup`).
- **Kungaprovet:** låses upp vid titel 16. 50 slumpade former från hela NT i rad utan fel och utan ledtråd (`KING_LEN`). Klarat prov sparas i `profiles.king_at`.
- **Statistik:** totalt antal parsade ord, andel rätt och fel och en linjegraf över de senaste 14 dagarna (`statsHTML`).
- **Att öva på:** träffsäkerhet per fält, vanligaste förväxlingar och fenomen (`phenOf`, som läser sprängskissens delar och förklaringar). ”Öva mina svagheter” väljer former med `weakForms`.
- **Kapitel som fylls:** kapitelrutorna fylls nedifrån med grönt efter andelen inlärda ord (`wordMastery`: de två senaste svaren rätt, det senaste utan ledtråd).
- **Min kurs, Tyck till och Konto:** `profiles`, `feedback` (högst 200 tecken, kryssruta för citat) och `delete_my_account()`. Tabellerna finns i `supabase/mina-sidor.sql`.

### Testa lokalt

`crypto.subtle` kräver en säker kontext, så appen fungerar inte via `file://`. Kör i stället `python3 -m http.server 8000` i repots rotmapp och öppna `http://localhost:8000/login/`. Onepagern ligger på `http://localhost:8000`. Vill du testa appen okrypterad kan du skriva ut den sammanfogade appfilen till en temporär fil utanför repot.

## Data i appen (`D` i JS)

- `words`: `[kapitel, typ 'N'|'V', fullt uppslagsord, grundform, betydelse, principalformer]`. Kapitel 99 betyder ”Övriga”, alltså glosor utanför bokens kapitel.
- `forms`: `[form, ordindex, godkända parsningskoder skilda med '|', antal förekomster i NT, exempelreferens 'bcv.ordindex']`.
- `verses`: versers text, nycklade på bcv.
- `an` och `fa`: nedbrytningar och kopplingen form → kod → nedbrytning.
- `nt`: sprängskissens förklaringar som `[svenska, engelska]`.

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

- **Lägen överst** (`S.mode`): ”Fritt” (`free`) och en knapp per bok, till exempel ”Enligt Mounce” (`book` med `S.book`). Knapparna skapas ur boklistan, så Duff och Croy får egna knappar när de läggs tillbaka. Väljer man en bok fälls frågan ”Hur långt har du kommit i Mounce?” ut i samma ruta, med kapitelvalet för grammatiken. Nya användare får det fria läget. Sparade inställningar utan läge behåller bokläget.
- **Det fria läget** följer appens egen ordning i 15 sektioner (`SECTIONS` i `src/app.html`): första och andra deklinationen, tredje deklinationen, presens aktiv, presens medium/passiv, kontraherade verb, imperfekt, futurum aktiv/medium, aorist 1, aorist 2, aorist och futurum passiv, perfekt och pluskvamperfekt, presens particip, aorist och perfekt particip, konjunktiv samt infinitiv och imperativ.
  - `secOf` avgör sektionen för en form och en parsningskod. Deklinationen tas ur uppslagsformen (`declOf`), kontraherade verb ur grundformen (`isContract`) och aorist 1 eller 2 ur aoristens principalform (`isAor2`). Likvida verb hamnar i futurum och aorist 1.
  - Varje sektion anger vilka moment i `MOMENTS` den bygger på. Svarsalternativen omfattar allt t.o.m. den högsta valda sektionen (`secMoments`).
  - Ordförrådet väljs efter frekvens i NT (`S.vocab`: 100, 300 eller alla, `RANK`). Valda sektioner sparas i `S.secs`.
  - Framstegen räknas ur de sparade svaren, så de gäller i båda lägena.
- **Läroböckerna** (`S.book`: Mounce, Duff eller Croy). Varje bok har ett kapitel per ord (`D.books[].ch`, 99 = ”Övriga”) och en grammatiktabell (`gram`) som anger i vilket kapitel varje grammatiskt moment introduceras. Momenten har Mounces kapitelnummer som intern nyckel (`MOMENTS` i appen, `MOM` i `build.py`). Grammatiktabellerna ligger i `kurser/<bok>-grammatik.tsv`. Saknas ett moment där väljs nivån manuellt bland momenten i stället. Croys tabell är ifylld från bokens innehållsförteckning. Duffs bygger på kapitelrubrikerna och ordlistan, och några rader är tolkningar (se kolumnen `källa`). Former utanför indikativ (particip, infinitiv, konjunktiv, imperativ) kräver både sitt modusmoment och sitt tempusmoment (`needs` och `tenseKey` i appen), eftersom Croy tar upp infinitiv redan i lektion 2. Inställningarna sparas per bok i `S.by`.
- Ord från Duff och Croy som inte finns i Mounces lista läggs till automatiskt, utom oböjliga ord.
- **Kunskapsnivå och glosor väljs separat.** `S.level` är alltid ett kapitel och styr grammatiken (`levelChs`, `clampLevel`). Utan sparad nivå blir den det högsta valda kapitlet. Kapitelvalet styr glosorna. Kapitlet som motsvarar nivån får en guldfärgad outline i kapitelrutnätet.
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
- **Lagring:** `localStorage` används för `kop-settings`, `kop-life`, `kop-tour` och `kop-key-<id>`, där den sista sparar inloggningen för ”kom ihåg mig”. Läsningar och skrivningar är alltid inslagna i try/catch.
- **Språk:** svenska och engelska, valt med flaggorna uppe till höger (`S.lang` i `kop-settings`). Utan sparat val blir det svenska om webbläsaren har svenska bland sina språk, annars engelska. All gränssnittstext ligger i `T` (meningar) och `LBL` (grammatiska termer, bibelböcker, nivåer) i `src/app.html`; använd `tx('nyckel')` och lägg alltid till texten på båda språken. Fast text i HTML:en märks med `data-i`/`data-ia`. Inloggningssidan har en egen liten ordlista och läser och skriver samma `kop-settings.lang`. Sprängskissens förklaringar skrivs på svenska i `morph.py` och översätts i bygget med mallarna i `scripts/noter_en.py`. De sparas i `nt` som `[svenska, engelska]`, och `an` pekar på dem med index. Lägg alltid till en engelsk mall när du lägger till en ny förklaring.
- **Tangentbord:** Enter kontrollerar svaret och går sedan vidare till nästa ord.
- **Guiden** (`startTour`, `setupTour`, `quizTour`) visas första gången på startsidan och första gången i övningen: en guldram runt det som förklaras och ett kort med Fortsätt (eller Enter) och Hoppa över guiden. Övningsguiden visar den riktiga uppdelningen av första formen i stegen Dela upp ordet och Visa etiketter, och första formen väljs helst bland dem med flest delar. Övningsguidens sista steg pekar på valknapparna. Första gången man når en nivå ersätts popupen av ett guidekort som pekar på Mina sidor (`levelTour`). Kortet visas när omgången är slut, eftersom knappen inte finns i övningens toppmeny. Guidekortet är guldfärgat med mörk text, så att det skiljer sig från appens blå. Visade guider sparas i `kop-tour`, och länken Visa guiden igen längst ned på startsidan nollställer dem.

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
- Principalformer: genererade med greek-inflexion av James Tauber (MIT-licens).
- Kapitelindelning: Mounce, *Basics of Biblical Greek* (privat kursfil).
- Text: SBL Greek New Testament.
- Morfologi: MorphGNT (github.com/morphgnt/sblgnt).
