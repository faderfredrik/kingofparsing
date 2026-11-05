# King of parsing 👑

Träna parsning av koine-grekiska substantiv och verb, kapitel för kapitel enligt Bill Mounce, *Basics of Biblical Greek*.

## Funktioner

- Formerna är verkliga former ur Nya testamentet, totalt cirka 8 400 former av 821 glosor.
- Kunskapsnivån och glosorna väljs separat. Du kan till exempel öva på glosor från kapitel 17 med grammatiken t.o.m. kapitel 25. Med automatisk nivå följer grammatiken det högsta valda kapitlet.
- Tvetydiga former godkänns för alla korrekta parsningar.
- Efter varje svar bryts formen ned i sina delar (prefix, augment, reduplikation, stam, tempusform, bindevokal och ändelse), med förklaringar av ljudförändringarna. Varje nedbrytning är kontrollerad mot den verkliga formen.
- Efter varje svar visas ett exempel ur NT, där ordet är markerat.
- I slutet av varje omgång får du en sammanfattning och kan öva på de former du missade.
- Inställningar och statistik sparas i webbläsaren (localStorage).

## Lösenordsskydd

`index.html` är krypterad med AES-256, och nyckeln tas fram ur lösenordet med PBKDF2 i 600 000 iterationer.

- Repot innehåller varken lösenordet eller några glosor i klartext.
- Den som inte har lösenordet ser bara inloggningssidan.
- ”Kom ihåg mig” sparar nyckeln i webbläsaren, så att man slipper logga in igen på samma enhet.

Byt lösenord så här:

1. Kör build-skriptet igen och ange det nya lösenordet.
2. Ladda upp den nya `index.html`.

Gamla sparade inloggningar slutar då att fungera.

## Publicera med GitHub Pages

1. Skapa ett nytt repo på github.com, till exempel `king-of-parsing`.
2. Välj **Add file → Upload files** och dra in innehållet i den här mappen. Ladda upp själva filerna, inte mappen.
3. Gå till **Settings → Pages**. Välj **Deploy from a branch**, sedan `main` och mappen `/ (root)`, och klicka på **Save**.
4. Efter någon minut ligger appen på `https://<ditt-användarnamn>.github.io/king-of-parsing/`.

## Struktur

| Fil | Innehåll |
|---|---|
| `index.html` | Den färdiga, krypterade appen: en enda fil som innehåller all data |
| `src/login.html` | Inloggningssidan |
| `src/app.html` | Mallen, alltså appens HTML, CSS och JavaScript utan data |
| `scripts/morph.py`, `scripts/analyze.py` | Motorn för morfologisk nedbrytning |
| `scripts/build.py` | Bygger om `index.html` från glosdatabasen och MorphGNT |

Gör så här för att ändra något:

1. Redigera `src/app.html`.
2. Kör `python3 scripts/build.py` med databasen `glosor.sqlite` i mappen `scripts/`. Skriptet frågar efter lösenordet och kräver Python-paketet `cryptography` (`pip install cryptography`).

Skriptet laddar ned MorphGNT automatiskt. Databasen `glosor.sqlite` ingår inte i repot.

## Källor

- Glosor: Bill Mounce, *Basics of Biblical Greek*.
- Grekisk text: SBL Greek New Testament (SBLGNT).
- Morfologi: MorphGNT, https://github.com/morphgnt/sblgnt
