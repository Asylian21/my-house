# Knižnica dokumentácie na /docs

Stránka `/docs` je samostatná knižnica aktuálneho C/B/B. Nahrádza pôvodnú dokumentačnú vetvu rozcestníka. Pôdorys, model ani konštrukčné rozhodnutia nemení; existujúce manuály a H200 stránky zostávajú dostupné.

## Obsah a ovládanie

- Úvod obsahuje náhľady domu a katedrálového stropu. Zložka **Vizualizácie domu** (`/docs?folder=visualizations`) ponúka 7 exteriérov a 3 interiérové zábery z hlavného 3D modelu C/B/B, s popismi, zväčšením, šípkami, miniatúrami a stiahnutím JPG 2 400 × 1 500 px. Štyri strany dopĺňajú tri šikmé pohľady; obývačka je zachytená smerom ku štítu aj ku kuchyni.
- Vizualizácie sa dajú nájsť cez spoločné vyhľadávanie a filter JPG. Odkaz uchováva konkrétny záber; funguje Späť/Vpred, Escape a návrat focusu na kartu. Ide o datované snímky modelu, nie fotografie hotovej stavby.
- Vnorené zložky obsahujú výkresy, správy, rozhodnutia, obrázky, modelové údaje a výslovne nahradené archívne riešenie.
- Všetkých 25 listov je samostatne dostupných ako farebné aj čiernobiele PDF. Počet listov sa uvádza oddelene od počtu súborov.
- Kompletné sady majú náhľad po jednotlivých listoch; obrázky sú vektorové SVG, s priblížením do 250 %. Sťahovanie poskytuje PDF, nie snímku náhľadu.
- Markdown správy sa čítajú priamo vrátane tabuliek, zoznamov, zdrojov a odkazov na známe dokumenty. Nevykonáva sa HTML zo správ. Neznáme lokálne cesty ani nebezpečné URL sa nemenia na navigáciu.
- Vyhľadávanie kontroluje názov, kód, názov súboru a obsah v celej knižnici, bez závislosti od diakritiky. Vyčistenie vyhľadávania vráti vybranú zložku. Typ a stav sa filtrujú samostatne.
- Odkaz uchováva zložku, vyhľadávanie, filtre, zoradenie, zoznam/mriežku a otvorený súbor. Fungujú priame odkazy, opätovné načítanie a Späť/Vpred.
- Náhľad má chybový stav a opakovanie načítania. Mobil má priamy download v päte náhľadu; menu zložiek presúva a drží focus, Escape ho zavrie. Podporované je tmavé zobrazenie a obmedzenie animácií.

Stav `coordination` znamená **nevydané na realizáciu**. Aktuálny výkres nie je automaticky schválený stavebný podklad. Súčasné H200 zostáva medzi aktuálnymi správami; štúdia 274 mm je označená ako archív.

## Vstupy a obnovovanie

Typový kontrakt a vyhľadávanie: `lib/document-library.ts`. Manifest: `lib/document-library.generated.json`. UI: `app/docs/document-library.tsx`, `document-markdown.tsx` a `document-library.css`.

Vizualizácie sú verzované v `public/visualizations/cbb/`, nezávisle od privátnych PDF exportov. `lib/house-visualizations.ts` ich pripája ku knižnici z manifestu `lib/house-visualizations.generated.json`. Po zmene 3D modelu ich obnoví `node scripts/house-visualizations/capture.mjs` proti serveru na porte 3001 (iný server cez `DOM_TEST_URL`). Polohy kamier a popisy sú v `scripts/house-visualizations/views.mjs`. Snímanie overí B/B, pripravenosť Babylon scény aj ArchViz, rozlíšenie a chyby načítania; mení len kamery a skrýva ovládacie a katastrálne vrstvy. Geometria ani materiály modelu sa neupravujú. Náhľady 800 × 500 px sa renderujú samostatne, takže galéria nenačítava plné obrázky vopred. Existujúce snímky sa pri `docs:library` nemenia.

`npm run docs:library` vytvára knižnicu z existujúcich výkresových exportov a správ. Príkaz je súčasťou `predev`, `prebuild` a záveru `docs:drawings`; po obnove výkresov sa teda knižnica obnoví rovnakým postupom. Kontrola odtlačkov umožňuje vynechať nezmenený export, ale neakceptuje chýbajúce súbory alebo neaktuálny manifest.

Privátne zdrojové PDF ostávajú v `output/pdf/`, generované lokálne aktíva pod `public/documents/` sú ignorované Gitom. Manifest je verzovateľný. Na inom stroji sú potrebné zdrojové súbory a runtime podľa `scripts/document-library/README.md`. Príkaz `node scripts/document-library/generate.mjs --check` overuje úplnosť a aktuálnosť bez zmeny súborov.

Sťahované súbory majú iba explicitne vygenerované verejné cesty; aplikácia neposkytuje univerzálny filesystem endpoint. Táto úprava nič nepublikuje ani nenahráva na hosting.

## Kontroly

`npx vitest run tests/document-library.test.ts --config vitest.config.ts` kontroluje scenáre vyhľadávania a filtrov, všetky listy, stav SM30/R7 a archívu, odkazy a skutočné veľkosti stiahnuteľných súborov.

Pri vizuálnej QA treba kontrolovať desktop aj mobil, náhľad výkresu a dlhej správy, listovanie sady, priblíženie, sťahovanie, priamy odkaz, Späť/Vpred, nulový výsledok a opakovanie po chybe načítania. Lokálna QA neznamená publikovanie alebo statické overenie dokumentácie.

Galériu a odtlačky obrázkov overí `node scripts/house-visualizations/verify.mjs`; desktopové aj mobilné snímky a výsledok uloží do `output/playwright/house-visualizations/`. Pred prijatím obnovených záberov treba vizuálne skontrolovať všetky kamery, najmä zakrytie fasády vegetáciou a čitateľnosť katedrálového stropu.
