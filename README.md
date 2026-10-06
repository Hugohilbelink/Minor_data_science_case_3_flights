# Minor_data_science_case_3_flights

Interactief Streamlit-dashboard over Zürich Airport in 2019–2020, gemaakt voor Case 3 van de Minor Data Science. De 17 aangeleverde datasets zijn opgenomen: het rooster, het luchthavenregister, Meteostat-weer en 14 profielbestanden van zeven Amsterdam–Barcelona-vluchten.

## Starten

Python 3.14 (lokaal getest en gekozen voor Streamlit Cloud). Vanuit een schone clone:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Geen API-key, handmatige uitpakstap of absolute lokale paden nodig. De ZIP wordt rechtstreeks gelezen. Streamlit Community Cloud: repository `Hugohilbelink/Minor_data_science_case_3_flights`, branch `main`, entrypoint `app.py`, Python 3.14.

## Verhaallijn

1. **Overzicht**: hoofdvraag, verkeer 2019–2020 en aandeel late vertrekken.
2. **Verkeer door de tijd**: aankomst/vertrek, kalendervergelijking, aggregatie, zoom en gaten.
3. **Bestemmingen**: ICAO-koppeling, log-kleurkaart, gebied/landselectie en routeverdieping.
4. **Vertraging & weer**: dagkoppeling, regen/droogvergelijking binnen jaren, uur/type/baan/afstand en verdeling.
5. **Voorspelling**: chronologische vergelijking van baselines, Ridge en boosting; aparte test en stresstest, empirische foutband en foutanalyse.
6. **Vluchtprofielen**: alle zeven vluchten en beide resoluties, hoogte/koers/snelheid, route en broninspectie; niet gekoppeld aan Zürich.
7. **Data & verantwoording**: inspectie vóór analyse, ingrepen met aantallen, ongewijzigde bronnen, koppeldekking, gevoeligheid en bronvermelding.
8. **Presenteren**: live spreekroute van 9,5 minuut en koppeling met de rubric Uitstekend.

## Kernuitkomsten

Het rooster bevat 242.738 bewegingen in 2019 en 80.723 in 2020 (−66,7%). Het aandeel vertrekken ≥15 minuten te laat daalt van 30,9% naar 14,7%. De 7-daags-gemiddelde-baseline wint op validatie; test-MAE november–december 2019 is circa 2,85 min op de gemiddelde positieve vertrekvertraging per dag. Dat is geen voorspelling voor een individuele vlucht of voor het huidige jaar.

## Welke bestanden zijn nodig?

| Bestand | Functie |
|---|---|
| `app.py` | Streamlit-interface en grafieken; startbestand |
| `data_pipeline.py` | Data inlezen, controleren en koppelen |
| `modeling.py` | Baselines, voorspelmodellen en evaluatie |
| `data_sources.zip` | Alle 17 originele CSV-/Excel-bestanden, ongewijzigd gebundeld |
| `requirements.txt` | Python-bibliotheken voor de installatie |
| `SOURCES.md` | Bronvermelding en verantwoording, ook zichtbaar in de app |
| `manifest.json` | Bestandslijst en SHA-256-controlesommen van de data |
| `README.md` | Startinstructies en uitleg |
| `.gitignore` | Houdt caches, lokale omgevingen en secrets buiten GitHub |

De eerste zes bestanden zijn nodig om de complete app te draaien. De laatste drie zorgen voor controleerbaarheid en een duidelijke overdracht. Alle negen blijven in deze repository.

De ZIP is bij het bouwen gemaakt van de los aangeleverde bestanden. Het rooster is circa 32 MB, groter dan de limiet voor een los bestand via de GitHub-webupload. De ZIP is circa 14,6 MB. Er zijn geen datasets samengevoegd, aangepast of weggelaten; uitpakken is niet nodig voor het dashboard.

## Reproduceerbaarheid en controle

De vaste data is opgenomen, dus een schone clone werkt zonder downloads of hulpscripts. `manifest.json` bevat per bronbestand de SHA-256; bronvermelding, aannames en code-documentatie staan in [SOURCES.md](SOURCES.md).

Lokale onderhoudsscripts voor tests en optionele nieuwe downloads staan in de naastgelegen map `onderhoud`, buiten de publicatiemap. Ze zijn niet nodig voor Streamlit. De acht datatests en de pagina-/filtercontroles zijn uitgevoerd; kaart, voorspelling en profieldata zijn ook online gecontroleerd.

De app is ontworpen op de hoogste rubricbeschrijvingen; de feitelijke beoordeling en live presentatie blijven aan docent en groep.
