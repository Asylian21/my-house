# Trávnik parcely v natívnej scéne

Plocha `DOM_00001` / `MAT_0001` (`real-grass`) v exporte predstavuje trávnik
parcely. Natívny materiál pôvodne prenášal iba farbu a drsnosť, takže plocha
pri terase vyzerala ako svetlý betón. Recept v `scripts/unreal/materials.py`
teraz používa pôvodné projektové `lawn-albedo.jpg` a `lawn-normal.jpg`.

Geometria a kolízie vychádzajú zo spoločného exportu. Babylon používa UV0
s násobkom 12 × 10 a silou normály 0,4. Export zachováva surové UV0, ale
neprenáša túto transformáciu textúry; natívny graf ju preto obnovuje pre oba
samplery. Albedo má sRGB, normála lineárne vzorkovanie s otočeným zeleným
kanálom a obe textúry opakovanie v oboch osiach. Ide o existujúcu projektovú
textúru, nie o fotografický záznam trávnika na pozemku.

## Import z 8. septembra 2026

[Úspešný import](../output/unreal/lawn-native-import-2-process.json) skončil
s exit 0 za 43,30 s. Načítal všetkých 1 878 aktívnych objektov a žiadny archívny
objekt; maximálna odchýlka natívnych bounds bola 0,009765625 mm. Kolízna
validácia skončila bez chýb. Trávnik má v natívnom LOD0 27 trojuholníkov a jeden
UV kanál. Kontrola živého grafu potvrdila spoločný uzol UV0 s násobkom 12 × 10.
Samotný počet trojuholníkov nepreukazuje zhodu všetkých UV hodnôt.

Zmena spoločného materiálového skriptu vyžadovala novú nemennú revíziu
vstupného kontraktu nábytku. Pôvodné vstupy a historické reporty zostali
zachované. Svietidlo prešlo jednorazovým obnovením pôvodného zdrojového
priradenia a následným bežným importom; výsledok opäť overil uložený materiál
s rovnakými 800 lm a 2700 K. Deväť dubových materiálov, ostatných 149 drevených
priradení a existujúci TV nábytok prešli kontrolami uloženia a opätovného načítania.

Prvý import a prvé spustenie jednorazového pomocného skriptu zlyhali pred
úpravou mapy. Ich logy zostali zachované. Bežný import nepridáva výnimku,
ktorá by povoľovala zastaraný materiálový kontrakt.

Po úprave prešlo 461 Node testov, 33 testov dubových materiálov a 69 testov
svietidla. Import nie je potvrdením fotorealizmu ani výkonu.

## Uložený materiál a skutočný render

[Samostatný čítací proces](../output/unreal/lawn-native-readback/native-286932dd-ad40-4140-9473-7393d1444122/receipt.json)
skončil s exit 0 a potvrdil uložené priradenie, spoločné UV súradnice oboch
textúr, ich vzorkovanie a zhodu vstupných bajtov pred/po kontrole. Nemenil
assety ani pôvodné importné reporty. Jednotlivé UV hodnoty vrcholov a celý
shader graf touto kontrolou porovnané neboli.

Nový balík vznikol 8. septembra o 18:56 UTC. [4K záber terasy](../output/unreal/runtime/launch-services-terrace-ebfedbfa-39dc-40d4-8738-424ba9b639b7/capture.png)
vizuálne potvrdil odstránenie bledej plochy. Aplikácia prešla kontrolou
LaunchServices, vstupu do enginu, prístupnosti, natívneho 4K render targetu,
normálneho ukončenia cez Cmd-Q a nezmeneného obsahu balíka. Tento konkrétny
beh mal iba 62/300 snímok aplikácie v popredí; jeho časovanie nepoužívame ako
meranie interaktívneho výkonu. Samostatné úspešné meranie aktuálneho interiéru
je v [runtime QA](unreal-runtime-qa.md).

Trávnik stále pôsobí rovnomerne a plocho. Najvýraznejší zostávajúci problém
tohto pohľadu je pravidelné opakovanie kresby dreva terasy. Vizuálna zhoda
s fotografiou pozemku ani fotorealizmus celej scény zatiaľ nie sú dosiahnuté.
