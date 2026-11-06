# Engelska versioner av sprängskissens förklaringar.
# morph.py skriver förklaringarna på svenska (och använder dem internt), så här
# översätts varje färdig förklaring med en mall. Saknas en mall stoppas bygget,
# så att ingen förklaring visas på fel språk. Lägg till en rad här när du
# lägger till en ny förklaring i morph.py.
import re

_G = r'(.+?)'  # en grekisk bokstavsföljd eller annat infogat värde
MALLAR = [
    (r'Utan personändelse förlängs bindevokalen ο till ω\.', 'With no personal ending, the connecting vowel ο lengthens to ω.'),
    (r'ντ kan inte stå sist i ordet: τ faller bort och ο förlängs till ω\.', 'ντ cannot stand at the end of a word: τ drops out and ο lengthens to ω.'),
    (_G + r' kan inte stå sist i ett grekiskt ord och faller bort\.', r'\1 cannot stand at the end of a Greek word and drops out.'),
    (r'Bindevokalen ε förlängs till ει före ς\.', 'The connecting vowel ε lengthens to ει before ς.'),
    (r'σ i ändelsen faller bort mellan två vokaler\.', 'The σ of the ending drops out between two vowels.'),
    (r'Likvida verb: σ i εσ faller bort mellan vokaler\.', 'Liquid verb: the σ of εσ drops out between vowels.'),
    (r'σ i stammen faller bort mellan vokaler\.', 'The σ of the stem drops out between vowels.'),
    (r'Kontraktion: ' + _G + r'\.', r'Contraction: \1.'),
    (r'σ \+ σ förenklas till ett σ\.', 'σ + σ is simplified to a single σ.'),
    (_G + r' faller bort före ' + _G + r', och ' + _G + r' förlängs till ' + _G + r'\.', r'\1 drops out before \2, and \3 lengthens to \4.'),
    (_G + r' faller bort före ' + _G + r'\.', r'\1 drops out before \2.'),
    (r'Stammen börjar på ευ, som här inte förlängs, så augmentet syns inte\.', 'The stem begins with ευ, which is not lengthened here, so the augment is not visible.'),
    (r'Stammen börjar på ευ, som här inte förlängs, så reduplikationen syns inte\.', 'The stem begins with ευ, which is not lengthened here, so the reduplication is not visible.'),
    (r'Stammen börjar redan på lång vokal \(' + _G + r'\), så augmentet syns inte\.', r'The stem already begins with a long vowel (\1), so the augment is not visible.'),
    (r'Stammen börjar redan på lång vokal \(' + _G + r'\), så reduplikationen syns inte\.', r'The stem already begins with a long vowel (\1), so the reduplication is not visible.'),
    (r'Stammen börjar på vokal, så augmentet förlänger den: ' + _G + r' \(temporalt augment\)\.', r'The stem begins with a vowel, so the augment lengthens it: \1 (temporal augment).'),
    (r'Stammen börjar på vokal, så reduplikationen förlänger den: ' + _G + r'\.', r'The stem begins with a vowel, so the reduplication lengthens it: \1.'),
    (r'Prepositionens slutvokal faller bort före augmentet \(' + _G + r'\)\.', r'The final vowel of the preposition drops out before the augment (\1).'),
    (r'Prepositionens slutvokal faller bort före reduplikationen\.', 'The final vowel of the preposition drops out before the reduplication.'),
    (r'ἐκ skrivs ἐξ före vokal\.', 'ἐκ is written ἐξ before a vowel.'),
    (r'Prepositionen får tillbaka sin grundform ' + _G + r' före augmentet\.', r'The preposition returns to its basic form \1 before the augment.'),
    (r'ο \+ ι: vokalen förlängs till ω och ι skrivs under \(ῳ\)\.', 'ο + ι: the vowel lengthens to ω and the ι is written as a subscript (ῳ).'),
    (_G + r' \+ ι: ι skrivs under \(' + _G + r'\)\.', r'\1 + ι: the ι is written as a subscript (\2).'),
    (r'Stamvokalen ' + _G + r' sväljs av ändelsen ων\.', r'The stem vowel \1 is absorbed by the ending ων.'),
    (r'Stamvokalen ' + _G + r' faller bort före ου\.', r'The stem vowel \1 drops out before ου.'),
    (r'Stamvokalen ο faller bort före neutrumändelsen α\.','The stem vowel ο drops out before the neuter ending α.'),
    (r'Stamvokalen ο blir ε i vokativ singular\.', 'The stem vowel ο becomes ε in the vocative singular.'),
    (_G + r' drar ihop sig till ' + _G + r'\.', r'\1 contract to \2.'),
    (_G + r' skrivs ' + _G + r'\.', r'\1 is written \2.'),
    (_G + r' blir ' + _G + r'\.', r'\1 becomes \2.'),
    (r'ν på slutet är ett rörligt ny \(ν ephelkystikon\)\.', 'The final ν is a movable nu (ν ephelkystikon).'),
    (r'Kontraktionsvokalen ' + _G + r' förlängs till ' + _G + r' före tempusformen\.', r'The contract vowel \1 lengthens to \2 before the tense formative.'),
    (r'Kontraktionsvokalen ' + _G + r' förlängs till ' + _G + r'\.', r'The contract vowel \1 lengthens to \2.'),
    (r'Pluskvamperfekt saknar ofta augment i koine\.', 'The pluperfect often lacks the augment in Koine.'),
    (r'Efter andra bokstäver än ε, ι och ρ skiftar α till η i genitiv och dativ singular\.', 'After letters other than ε, ι and ρ, α shifts to η in the genitive and dative singular.'),
    (r'I plural slutar stammen på α\.', 'In the plural the stem ends in α.'),
]
_KOMPILERADE = [(re.compile(m + r'\Z'), e) for m, e in MALLAR]

# Ett infogat värde får bara vara grekiska och enkla tecken, aldrig svenska ord.
_TILLATET = re.compile(r'[Ͱ-Ͽἀ-῿̀-ͯ +→]*\Z')


def engelska(not_sv):
    for m, e in _KOMPILERADE:
        tr = m.match(not_sv)
        if tr and all(_TILLATET.match(g or '') for g in tr.groups()):
            return tr.expand(e)
    raise SystemExit(f'Saknar engelsk översättning för förklaringen: {not_sv}\n'
                     'Lägg till en mall i scripts/noter_en.py.')
