# LLM Parsing Validation Report

Generated: 2026-05-27 11:32:44

## Summary

- Total parsers tested: 47
- Total URLs tested: 139
- Total issues found: 70
- PASS: 12 | WARN: 35 | FAIL: 0
- NO_URLS: 0 | NO_RESULTS: 0 | SKIPPED: 0

## Issue Breakdown

| Issue | Count |
|-------|------:|
| concept is missing | 43 |
| content too short after cleaning | 11 |
| LLM returned None | 9 |
| preface is missing | 4 |
| artworks[18] missing work_title | 1 |
| start_date invalid format (expected YYYY-MM-DD): '2018' | 1 |
| city is missing | 1 |

## baltic (BALTIC) — PASS

- URLs found: 6
- URLs tested: 3
- Issues: 0

### https://baltic.art/whats-on/XUe-milly-thompsonmy-body-temperature-is-feeling-good/
- **Title**: `Milly Thompson My Body Temperature is Feeling Good`
- **Dates**: 2026-03-28 → 2026-08-30
- **Curators**: 0
- **Artworks**: 4
- **Concept length**: 204 chars
- **Preface length**: 294 chars
- **No issues detected**

### https://baltic.art/whats-on/XUi-foundation-pressstarting-lines/
- **Title**: `Starting Lines`
- **Dates**: 2026-04-18 → 2026-08-30
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 53 chars
- **Preface length**: 144 chars
- **No issues detected**

### https://baltic.art/whats-on/Xqr-foundation-press-wednesday-workshops-morning-edition/
- **Title**: `Foundation Press Wednesday Workshops: Morning Edition`
- **Dates**: 2025-04-01 → 2025-08-26
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 63 chars
- **Preface length**: 134 chars
- **No issues detected**

## beyeler (Fondation Beyeler) — WARN

- URLs found: 4
- URLs tested: 3
- Issues: 2

### https://www.fondationbeyeler.ch/en/exhibitions/past-exhibitions
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - LLM returned None

### https://www.fondationbeyeler.ch/en/exhibitions/pierre-huyghe
- **Title**: `Pierre Huyghe`
- **Dates**: ? → ?
- **Curators**: 1
- **Artworks**: 1
- **Concept length**: 68 chars
- **Preface length**: 59 chars
- **No issues detected**

### https://www.fondationbeyeler.ch/en/exhibitions/ruth-asawa
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - LLM returned None

## barbican (Barbican Centre) — WARN

- URLs found: 34
- URLs tested: 3
- Issues: 1

### https://www.barbican.org.uk/whats-on/2025/event/concrete-and-clay-archiving-the-barbican
- **Title**: `Concrete and Clay`
- **Dates**: 2025-02-10 → 2027-01-01
- **Curators**: 1
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 156 chars
- **Issues**:
  - concept is missing

### https://www.barbican.org.uk/whats-on/2025/series/encounters-giacometti
- **Title**: `Encounters: Giacometti`
- **Dates**: 2025-09-03 → 2026-05-31
- **Curators**: 0
- **Artworks**: 4
- **Concept length**: 64 chars
- **Preface length**: 158 chars
- **No issues detected**

### https://www.barbican.org.uk/whats-on/2026/event/1996-a-celebration-of-the-wildest-year-of-britains-wildest
- **Title**: `1996: 30 years on`
- **Dates**: 2026-04-16 → 2026-09-19
- **Curators**: 1
- **Artworks**: 7
- **Concept length**: 77 chars
- **Preface length**: 139 chars
- **No issues detected**

## berlin_biennale (Berlin Biennale) — WARN

- URLs found: 30
- URLs tested: 3
- Issues: 2

### https://berlinbiennale.de/de/1362/uber-uns
- **Title**: `Berlin Biennale für zeitgenössische Kunst`
- **Dates**: ? → ?
- **Curators**: 40
- **Artworks**: 0
- **Concept length**: 134 chars
- **Preface length**: 143 chars
- **No issues detected**

### https://berlinbiennale.de/de/1363/team-der-berlin-biennale
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - LLM returned None

### https://berlinbiennale.de/de/1364/kontakt
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - LLM returned None

## brooklyn_museum (Brooklyn Museum) — WARN

- URLs found: 23
- URLs tested: 3
- Issues: 1

### https://www.brooklynmuseum.org/exhibitions/american-art
- **Title**: `Toward Joy: New Frameworks for American Art`
- **Dates**: ? → ?
- **Curators**: 6
- **Artworks**: 2
- **Concept length**: 84 chars
- **Preface length**: 393 chars
- **No issues detected**

### https://www.brooklynmuseum.org/exhibitions/ancient_egyptian_art
- **Title**: `Ancient Egyptian Art`
- **Dates**: ? → ?
- **Curators**: 3
- **Artworks**: 8
- **Concept length**: 72 chars
- **Preface length**: 493 chars
- **No issues detected**

### https://www.brooklynmuseum.org/exhibitions/arts_asia
- **Title**: `Arts of Asia`
- **Dates**: ? → ?
- **Curators**: 3
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 221 chars
- **Issues**:
  - concept is missing

## kanazawa21 (21st Century Museum) — PASS

- URLs found: 5
- URLs tested: 3
- Issues: 0

### https://www.kanazawa21.jp/en/exhibitions/data_list.php?g=61&d=499
- **Title**: `路上、お邪魔ですか？`
- **Dates**: 2026-04-25 → 2026-09-06
- **Curators**: 1
- **Artworks**: 2
- **Concept length**: 86 chars
- **Preface length**: 101 chars
- **No issues detected**

### https://www.kanazawa21.jp/en/exhibitions/data_list.php?g=61&d=500
- **Title**: `路上、お邪魔ですか？`
- **Dates**: 2026-04-25 → 2026-09-06
- **Curators**: 1
- **Artworks**: 2
- **Concept length**: 86 chars
- **Preface length**: 101 chars
- **No issues detected**

### https://www.kanazawa21.jp/en/exhibitions/data_list.php?g=65&d=1852
- **Title**: `路上、お邪魔ですか？`
- **Dates**: 2026-04-25 → 2026-09-06
- **Curators**: 1
- **Artworks**: 2
- **Concept length**: 86 chars
- **Preface length**: 101 chars
- **No issues detected**

## astrup_fearnley (Astrup Fearnley Museet) — WARN

- URLs found: 6
- URLs tested: 3
- Issues: 3

### https://afmuseet.no/en/exhibitions/#content
- **Title**: `Astrup Fearnley Collection`
- **Dates**: 2026-01-02 → 2026-12-30
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 57 chars
- **Issues**:
  - concept is missing

### https://afmuseet.no/en/exhibitions/?show=previous
- **Title**: `Grammars of Light`
- **Dates**: 2026-02-06 → 2026-05-10
- **Curators**: 1
- **Artworks**: 3
- **Concept length**: 0 chars
- **Preface length**: 97 chars
- **Issues**:
  - concept is missing

### https://www.afmuseet.no/en/exhibitions/astrup-fearnley-collection-2/
- **Title**: `Astrup Fearnley Collection`
- **Dates**: 2026-01-02 → 2026-12-30
- **Curators**: 0
- **Artworks**: 8
- **Concept length**: 0 chars
- **Preface length**: 106 chars
- **Issues**:
  - concept is missing

## documenta (Documenta) — PASS

- URLs found: 15
- URLs tested: 3
- Issues: 0

### https://documenta.de/en/retrospective/4-documenta
- **Title**: `documenta 4`
- **Dates**: 1968-06-27 → 1968-10-06
- **Curators**: 1
- **Artworks**: 10
- **Concept length**: 121 chars
- **Preface length**: 328 chars
- **No issues detected**

### https://documenta.de/en/retrospective/documenta
- **Title**: `documenta | documenta`
- **Dates**: 1955-07-16 → 1955-09-18
- **Curators**: 1
- **Artworks**: 14
- **Concept length**: 111 chars
- **Preface length**: 195 chars
- **No issues detected**

### https://documenta.de/en/retrospective/documenta-12
- **Title**: `documenta 12`
- **Dates**: 2007-06-16 → 2007-09-23
- **Curators**: 2
- **Artworks**: 6
- **Concept length**: 119 chars
- **Preface length**: 153 chars
- **No issues detected**

## kunsthal (Kunsthal Rotterdam) — WARN

- URLs found: 9
- URLs tested: 3
- Issues: 1

### https://www.kunsthal.nl/en/plan-your-visit/exhibitions/a-chair-and-you/
- **Title**: `A Chair and You`
- **Dates**: 2026-09-26 → 2027-01-31
- **Curators**: 1
- **Artworks**: 9
- **Concept length**: 80 chars
- **Preface length**: 164 chars
- **No issues detected**

### https://www.kunsthal.nl/en/plan-your-visit/exhibitions/benedikte-bjerre-en/
- **Title**: `When the wind blows`
- **Dates**: 2026-05-30 → 2026-11-01
- **Curators**: 0
- **Artworks**: 2
- **Concept length**: 117 chars
- **Preface length**: 129 chars
- **No issues detected**

### https://www.kunsthal.nl/en/plan-your-visit/exhibitions/floor-rieder-scratch-scratch-scratch/
- **Title**: `Scratch, scratch, scratch`
- **Dates**: 2026-03-21 → 2026-06-21
- **Curators**: 0
- **Artworks**: 2
- **Concept length**: 0 chars
- **Preface length**: 153 chars
- **Issues**:
  - concept is missing

## hamburger_bahnhof (Hamburger Bahnhof) — WARN

- URLs found: 14
- URLs tested: 3
- Issues: 1

### https://www.smb.museum/en/museums-institutions/hamburger-bahnhof/exhibitions/detail/annika-kahrs/
- **Title**: `Annika Kahrs: OFF SCORE`
- **Dates**: 2025-11-14 → 2026-05-03
- **Curators**: 1
- **Artworks**: 2
- **Concept length**: 0 chars
- **Preface length**: 155 chars
- **Issues**:
  - concept is missing

### https://www.smb.museum/en/museums-institutions/hamburger-bahnhof/exhibitions/detail/chanel-commission-klara-hosnedlova-embrace/
- **Title**: `CHANEL Commission: Klára Hosnedlová. embrace`
- **Dates**: 2025-05-01 → 2026-01-04
- **Curators**: 2
- **Artworks**: 1
- **Concept length**: 134 chars
- **Preface length**: 182 chars
- **No issues detected**

### https://www.smb.museum/en/museums-institutions/hamburger-bahnhof/exhibitions/detail/chanel-commission-lina-lapelyte-we-make-years-out-of-hours/
- **Title**: `CHANEL Commission: Lina Lapelytė. We Make Years Out of Hours`
- **Dates**: 2026-05-01 → 2027-01-10
- **Curators**: 2
- **Artworks**: 1
- **Concept length**: 72 chars
- **Preface length**: 201 chars
- **No issues detected**

## hammer_museum (Hammer Museum) — WARN

- URLs found: 7
- URLs tested: 3
- Issues: 3

### https://hammer.ucla.edu/exhibitions/2026/arthur-jafa-white-album
- **Title**: `Arthur Jafa: The White Album`
- **Dates**: 2026-03-14 → 2026-08-30
- **Curators**: 1
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 196 chars
- **Issues**:
  - concept is missing

### https://hammer.ucla.edu/exhibitions/2026/hammer-projects-mike-cloud
- **Title**: `Hammer Projects: Mike Cloud`
- **Dates**: 2026-03-28 → 2027-01-07
- **Curators**: 2
- **Artworks**: 4
- **Concept length**: 0 chars
- **Preface length**: 186 chars
- **Issues**:
  - concept is missing

### https://hammer.ucla.edu/exhibitions/2026/several-eternities-day-form-age-living-materials
- **Title**: `Several Eternities in a Day: Form in the Age of Living Materials`
- **Dates**: 2026-04-05 → 2026-08-23
- **Curators**: 2
- **Artworks**: 23
- **Concept length**: 72 chars
- **Preface length**: 201 chars
- **Issues**:
  - artworks[18] missing work_title

## leeum (Leeum Samsung Museum) — WARN

- URLs found: 4
- URLs tested: 3
- Issues: 1

### https://www.leeumhoam.org/leeum/exhibition/73?params=Y
- **Title**: `Leeum Museum of Art Exhibition`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 41 chars
- **Issues**:
  - concept is missing

### https://www.leeumhoam.org/leeum/exhibition/92?params=Y
- **Title**: `티노 세갈`
- **Dates**: 2026-03-03 → 2026-06-28
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 151 chars
- **Preface length**: 131 chars
- **No issues detected**

### https://www.leeumhoam.org/leeum/exhibition/93?params=Y
- **Title**: `다른 공간 안으로: 여성 작가들의 공감각적 환경 1956-1976`
- **Dates**: 2026-05-05 → 2026-11-29
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 91 chars
- **Preface length**: 115 chars
- **No issues detected**

## louisiana (Louisiana Museum) — PASS

- URLs found: 1
- URLs tested: 1
- Issues: 0

### https://louisiana.dk/en/exhibition/ragnar-kjartansson/
- **Title**: `Epic Waste of Love and Understanding`
- **Dates**: 2023-06-09 → 2023-10-22
- **Curators**: 1
- **Artworks**: 5
- **Concept length**: 67 chars
- **Preface length**: 94 chars
- **No issues detected**

## liverpool_biennial (Liverpool Biennial) — WARN

- URLs found: 21
- URLs tested: 3
- Issues: 1

### https://www.biennial.com/artists-directory/
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - LLM returned None

### https://www.biennial.com/creation-and-curation-with-young-people-at-mya/
- **Title**: `Creation and Curation with Young People - Liverpool Biennial x MYA SPACE`
- **Dates**: ? → ?
- **Curators**: 2
- **Artworks**: 2
- **Concept length**: 75 chars
- **Preface length**: 136 chars
- **No issues detected**

### https://www.biennial.com/curators-and-dates-announced-for-liverpool-biennial-2027/
- **Title**: `Liverpool Biennial 2027`
- **Dates**: 2027-06-05 → 2027-09-12
- **Curators**: 2
- **Artworks**: 0
- **Concept length**: 73 chars
- **Preface length**: 74 chars
- **No issues detected**

## kw_institute (KW Institute) — WARN

- URLs found: 31
- URLs tested: 3
- Issues: 1

### https://www.kw-berlin.de/en/about/board
- **Title**: `Board of KW Institute for Contemporary Art`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 138 chars
- **Issues**:
  - concept is missing

### https://www.kw-berlin.de/en/about/code-of-conduct
- **Title**: `Code of Conduct`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 124 chars
- **Preface length**: 113 chars
- **No issues detected**

### https://www.kw-berlin.de/en/about/mission-history
- **Title**: `Mission & History - KW Institute for Contemporary Art`
- **Dates**: ? → ?
- **Curators**: 4
- **Artworks**: 28
- **Concept length**: 100 chars
- **Preface length**: 218 chars
- **No issues detected**

## maxxi (MAXXI) — WARN

- URLs found: 54
- URLs tested: 3
- Issues: 1

### https://www.maxxi.art/en/events/11-plus-rooms/
- **Title**: `11 plus Rooms`
- **Dates**: 2026-11-27 → 2027-02-07
- **Curators**: 3
- **Artworks**: 1
- **Concept length**: 70 chars
- **Preface length**: 98 chars
- **No issues detected**

### https://www.maxxi.art/en/events/16-anni-maxxi/
- **Title**: `16 anni MAXXI: una giornata aperta, gratuita, per tutti`
- **Dates**: 2026-05-29 → 2026-05-29
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 59 chars
- **Issues**:
  - concept is missing

### https://www.maxxi.art/en/events/alberto-garutti/
- **Title**: `Alberto Garutti. Temporali`
- **Dates**: 2023-10-07 → 2026-10-10
- **Curators**: 1
- **Artworks**: 1
- **Concept length**: 64 chars
- **Preface length**: 108 chars
- **No issues detected**

## mca_australia (MCA Australia) — WARN

- URLs found: 361
- URLs tested: 3
- Issues: 3

### https://www.mca.com.au/exhibitions/#
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

### https://www.mca.com.au/exhibitions/11th-biennale-of-sydney/
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

### https://www.mca.com.au/exhibitions/12th-biennale-of-sydney/
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

## mca_chicago (MCA Chicago) — WARN

- URLs found: 11
- URLs tested: 3
- Issues: 2

### https://mcachicago.org/exhibitions/art-in-free-spaces
- **Title**: `Art in Free Spaces`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 6
- **Concept length**: 0 chars
- **Preface length**: 119 chars
- **Issues**:
  - concept is missing

### https://mcachicago.org/exhibitions/artists-in-residence
- **Title**: `Artists in Residence`
- **Dates**: 2011-01-01 → 2016-06-30
- **Curators**: 0
- **Artworks**: 4
- **Concept length**: 0 chars
- **Preface length**: 158 chars
- **Issues**:
  - concept is missing

### https://visit.mcachicago.org/exhibitions/atrium-project-edie-fake/
- **Title**: `Atrium Project: Edie Fake`
- **Dates**: ? → ?
- **Curators**: 1
- **Artworks**: 1
- **Concept length**: 97 chars
- **Preface length**: 175 chars
- **No issues detected**

## met (The Met) — WARN

- URLs found: 43
- URLs tested: 3
- Issues: 3

### https://www.metmuseum.org/en/exhibitions/past
- **Title**: `Filling in the Gaps: A Selection of Works by the 2026 Scholastic Art & Writing Awards New York City Gold Key Recipients`
- **Dates**: 2026-03-28 → 2026-05-18
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 0 chars
- **Issues**:
  - concept is missing
  - preface is missing

### https://www.metmuseum.org/exhibitions/a-kings-carpet-louis-xiv-and-the-savonnerie
- **Title**: `A King’s Carpet: Louis XIV and the Savonnerie`
- **Dates**: 2026-09-08 → 2028-03-05
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 188 chars
- **Issues**:
  - concept is missing

### https://www.metmuseum.org/exhibitions/afrofuturist-period-room
- **Title**: `Before Yesterday We Could Fly: An Afrofuturist Period Room`
- **Dates**: ? → ?
- **Curators**: 2
- **Artworks**: 4
- **Concept length**: 119 chars
- **Preface length**: 233 chars
- **No issues detected**

## lenbachhaus (Lenbachhaus) — PASS

- URLs found: 120
- URLs tested: 3
- Issues: 0

### https://www.lenbachhaus.de/en/program/exhibitions/details/19th-century
- **Title**: `19th Century Collection Presentation`
- **Dates**: 2013-05-01 → 2017-01-29
- **Curators**: 1
- **Artworks**: 6
- **Concept length**: 84 chars
- **Preface length**: 129 chars
- **No issues detected**

### https://www.lenbachhaus.de/en/program/exhibitions/details/aber-hier-leben-nein-danke-surrealismus-antifaschismus
- **Title**: `But Live Here? No thanks: Surrealism and Anti-fascism`
- **Dates**: 2024-10-15 → 2025-03-30
- **Curators**: 3
- **Artworks**: 12
- **Concept length**: 82 chars
- **Preface length**: 137 chars
- **No issues detected**

### https://www.lenbachhaus.de/en/program/exhibitions/details/after-expressionism
- **Title**: `After Expressionism`
- **Dates**: 2017-10-01 → 2021-01-10
- **Curators**: 0
- **Artworks**: 19
- **Concept length**: 148 chars
- **Preface length**: 187 chars
- **No issues detected**

## mori (Mori Art Museum) — WARN

- URLs found: 72
- URLs tested: 3
- Issues: 3

### https://www.mori.art.museum/en/exhibitions/2003/
- **Title**: `Happiness: A Survival Guide for Art and Life`
- **Dates**: 2003-10-18 → 2004-01-18
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 43 chars
- **Issues**:
  - concept is missing

### https://www.mori.art.museum/en/exhibitions/2004/
- **Title**: `2004 Exhibitions at Mori Art Museum`
- **Dates**: 2004-01-31 → 2005-03-13
- **Curators**: 0
- **Artworks**: 10
- **Concept length**: 0 chars
- **Preface length**: 86 chars
- **Issues**:
  - concept is missing

### https://www.mori.art.museum/en/exhibitions/2005/
- **Title**: `Hiroshi Sugimoto: End of Time`
- **Dates**: 2005-09-17 → 2006-01-09
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 52 chars
- **Issues**:
  - concept is missing

## momat (MOMAT) — PASS

- URLs found: 15
- URLs tested: 3
- Issues: 0

### https://www.momat.go.jp/exhibitions/561
- **Title**: `Hilma af Klint Exhibition`
- **Dates**: 2025-03-04 → 2025-06-15
- **Curators**: 0
- **Artworks**: 6
- **Concept length**: 119 chars
- **Preface length**: 296 chars
- **No issues detected**

### https://www.momat.go.jp/exhibitions/563
- **Title**: `記録をひらく 記憶をつむぐ`
- **Dates**: 2025-07-15 → 2025-10-26
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 138 chars
- **Preface length**: 172 chars
- **No issues detected**

### https://www.momat.go.jp/exhibitions/566
- **Title**: `アンチ・アクション　彼女たち、それぞれの応答と挑戦`
- **Dates**: 2025-12-16 → 2026-02-08
- **Curators**: 1
- **Artworks**: 14
- **Concept length**: 82 chars
- **Preface length**: 202 chars
- **No issues detected**

## maiiam (MAIIAM) — PASS

- URLs found: 25
- URLs tested: 3
- Issues: 0

### https://maiiam.com/en/exhibition/a-beast-a-god-and-a-line
- **Title**: `A beast, a god, and a line`
- **Dates**: 2020-11-14 → 2021-03-21
- **Curators**: 1
- **Artworks**: 8
- **Concept length**: 179 chars
- **Preface length**: 228 chars
- **No issues detected**

### https://maiiam.com/en/exhibition/cold-war-the-mysterious
- **Title**: `Cold War: the mysterious`
- **Dates**: 2022-03-12 → 2023-02-14
- **Curators**: 0
- **Artworks**: 7
- **Concept length**: 88 chars
- **Preface length**: 293 chars
- **No issues detected**

### https://maiiam.com/en/exhibition/diaspora-exit-exile-exodus-of-southeast-asia-exhibition
- **Title**: `Diaspora: Exit, Exile, Exodus of Southeast Asia`
- **Dates**: 2018-03-04 → 2018-10-01
- **Curators**: 1
- **Artworks**: 18
- **Concept length**: 110 chars
- **Preface length**: 274 chars
- **No issues detected**

## new_museum (New Museum) — WARN

- URLs found: 10
- URLs tested: 3
- Issues: 3

### https://www.newmuseum.org/exhibition/atrium-stair-klara-hosnedlova/
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

### https://www.newmuseum.org/exhibition/facade-tschabalala-self-art-lovers/
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

### https://www.newmuseum.org/exhibition/first-look-black-artist-burnout/
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

## museum_ludwig (Museum Ludwig) — PASS

- URLs found: 6
- URLs tested: 3
- Issues: 0

### https://www.museum-ludwig.de/en/home/exhibitions/2025
- **Title**: `Preview - Museum Ludwig, Köln 2026 Program`
- **Dates**: 2026-07-18 → 2027-04-07
- **Curators**: 3
- **Artworks**: 3
- **Concept length**: 118 chars
- **Preface length**: 175 chars
- **No issues detected**

### https://www.museum-ludwig.de/en/home/exhibitions/archive
- **Title**: `Archive - Museum Ludwig, Köln`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 109 chars
- **Preface length**: 117 chars
- **No issues detected**

### https://www.museum-ludwig.de/en/home/exhibitions/here-and-now-at-museum-ludwig-de/collecting-memories-from-turtle-island
- **Title**: `HERE AND NOW at Museum Ludwig. De/Collecting Memories from Turtle Island`
- **Dates**: ? → ?
- **Curators**: 2
- **Artworks**: 4
- **Concept length**: 114 chars
- **Preface length**: 134 chars
- **No issues detected**

## mplus (M+ Museum) — WARN

- URLs found: 38
- URLs tested: 3
- Issues: 1

### https://www.mplus.org.hk/en/exhibitions/all-star-video/
- **Title**: `All Star Video`
- **Dates**: 2026-02-14 → 2026-07-05
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 174 chars
- **Issues**:
  - concept is missing

### https://www.mplus.org.hk/en/exhibitions/canton-modern-art-and-visual-culture/
- **Title**: `Canton Modern: Art and Visual Culture, 1900s–1970s`
- **Dates**: 2025-06-28 → 2025-10-05
- **Curators**: 0
- **Artworks**: 11
- **Concept length**: 117 chars
- **Preface length**: 431 chars
- **No issues detected**

### https://www.mplus.org.hk/en/exhibitions/carsten-nicolai-endo-exo-phosphenes/
- **Title**: `Carsten Nicolai: ENDO EXO, PHOSPHENES`
- **Dates**: 2026-02-10 → 2026-07-31
- **Curators**: 0
- **Artworks**: 2
- **Concept length**: 73 chars
- **Preface length**: 196 chars
- **No issues detected**

## ngv (NGV) — WARN

- URLs found: 22
- URLs tested: 3
- Issues: 2

### https://www.ngv.vic.gov.au/exhibition/art-of-the-pacific-from-the-ngv-collection/
- **Title**: `Art of the Pacific: From the NGV Collection`
- **Dates**: 2025-11-15 → 2026-10-04
- **Curators**: 0
- **Artworks**: 16
- **Concept length**: 0 chars
- **Preface length**: 136 chars
- **Issues**:
  - concept is missing

### https://www.ngv.vic.gov.au/exhibition/bark-salon/
- **Title**: `Bark Salon`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 63 chars
- **Preface length**: 143 chars
- **No issues detected**

### https://www.ngv.vic.gov.au/exhibition/bearing-witness/
- **Title**: `Bearing Witness: Contemporary Asian art from the NGV Collection`
- **Dates**: 2026-04-18 → 2026-08-30
- **Curators**: 1
- **Artworks**: 9
- **Concept length**: 0 chars
- **Preface length**: 104 chars
- **Issues**:
  - concept is missing

## national_gallery_sg (National Gallery Singapore) — WARN

- URLs found: 10
- URLs tested: 3
- Issues: 1

### https://www.nationalgallery.sg/sg/en/exhibitions/After-the-Monsoon-Art-War-in-Southeast-Asia.html
- **Title**: `After the Monsoon: Art & War in Southeast Asia`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 102 chars
- **Issues**:
  - concept is missing

### https://www.nationalgallery.sg/sg/en/exhibitions/Fear-no-power.html
- **Title**: `Fear No Power: Women Imagining Otherwise`
- **Dates**: 2026-01-09 → 2026-11-15
- **Curators**: 0
- **Artworks**: 5
- **Concept length**: 69 chars
- **Preface length**: 255 chars
- **No issues detected**

### https://www.nationalgallery.sg/sg/en/exhibitions/He-Xiangning-Ink-Intent.html
- **Title**: `He Xiangning: Ink & Intent`
- **Dates**: 2026-04-01 → 2026-08-23
- **Curators**: 0
- **Artworks**: 11
- **Concept length**: 90 chars
- **Preface length**: 191 chars
- **No issues detected**

## palaistokyo (Palais de Tokyo) — PASS

- URLs found: 8
- URLs tested: 3
- Issues: 0

### https://palaisdetokyo.com/exposition/cheryl-marie-wade-la-derniere-performance-de-la-reine-mere-des-noueux/
- **Title**: `Cheryl Marie Wade, reine-mère des noueux`
- **Dates**: 2026-04-03 → 2026-09-13
- **Curators**: 2
- **Artworks**: 11
- **Concept length**: 124 chars
- **Preface length**: 159 chars
- **No issues detected**

### https://palaisdetokyo.com/exposition/globale-inversion-inversion/
- **Title**: `Globale Inversion Inversion`
- **Dates**: 2026-06-05 → 2026-09-13
- **Curators**: 2
- **Artworks**: 6
- **Concept length**: 95 chars
- **Preface length**: 129 chars
- **No issues detected**

### https://palaisdetokyo.com/exposition/les-ambassadeurs/
- **Title**: `LES AMBASSADEURS - JESSE DARLING`
- **Dates**: 2026-04-03 → 2026-09-13
- **Curators**: 1
- **Artworks**: 1
- **Concept length**: 91 chars
- **Preface length**: 490 chars
- **No issues detected**

## njpac (Nam June Paik Art Center) — WARN

- URLs found: 22
- URLs tested: 3
- Issues: 2

### https://njpart.ggcf.kr/exhibitions/253
- **Title**: `Circuits of Chance`
- **Dates**: 2026-03-19 → 2026-06-14
- **Curators**: 4
- **Artworks**: 16
- **Concept length**: 176 chars
- **Preface length**: 180 chars
- **No issues detected**

### https://njpart.ggcf.kr/exhibitions/255
- **Title**: `Cosmic Color Opera`
- **Dates**: 2026-04-30 → 2026-06-07
- **Curators**: 1
- **Artworks**: 3
- **Concept length**: 142 chars
- **Preface length**: 174 chars
- **No issues detected**

### https://njpart.ggcf.kr/exhibitions/more
- **Title**: `Nam June Paik, Ecologist of the Videosphere`
- **Dates**: 2026-05-11 → 2026-05-16
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 0 chars
- **Issues**:
  - concept is missing
  - preface is missing

## pompidou (Centre Pompidou) — WARN

- URLs found: 52
- URLs tested: 3
- Issues: 3

### https://www.centrepompidou.fr/en/program/calendar/event/182gDQs
- **Title**: `Nemtsov, Toraman, Poppe`
- **Dates**: 2026-06-13 → 2026-06-13
- **Curators**: 0
- **Artworks**: 3
- **Concept length**: 0 chars
- **Preface length**: 108 chars
- **Issues**:
  - concept is missing

### https://www.centrepompidou.fr/en/program/calendar/event/28Sv3dq
- **Title**: `Matisse, 1941-1954`
- **Dates**: 2026-03-24 → 2026-07-26
- **Curators**: 2
- **Artworks**: 13
- **Concept length**: 0 chars
- **Preface length**: 183 chars
- **Issues**:
  - concept is missing

### https://www.centrepompidou.fr/en/program/calendar/event/3WgaiDZ
- **Title**: `Dans les coulisses du festival`
- **Dates**: 2026-06-15 → 2026-06-15
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 103 chars
- **Issues**:
  - concept is missing

## psa (Power Station of Art) — WARN

- URLs found: 24
- URLs tested: 3
- Issues: 3

### https://www.powerstationofart.com/whats-on/exhibitions/a-walk-on-the-wild-side
- **Title**: `Power Station of Art`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 127 chars
- **Issues**:
  - concept is missing

### https://www.powerstationofart.com/whats-on/exhibitions/alvaro-siza-the-archive
- **Title**: `Power Station of Art`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 127 chars
- **Issues**:
  - concept is missing

### https://www.powerstationofart.com/whats-on/exhibitions/annette-messager
- **Title**: `Power Station of Art`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 127 chars
- **Issues**:
  - concept is missing

## saopaulo_biennial (São Paulo Biennial) — WARN

- URLs found: 50
- URLs tested: 3
- Issues: 1

### https://36.bienal.org.br/itinerancia/
- **Title**: `Itinerância - 36ª Bienal de São Paulo`
- **Dates**: 2025-09-06 → 2026-01-11
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 60 chars
- **Preface length**: 138 chars
- **No issues detected**

### https://bienal.org.br/agenda/
- **Title**: `36th São Paulo Biennial – Not Every Wanderer Walks Roads – Humanity as Practice`
- **Dates**: 2026-03-03 → 2026-08-16
- **Curators**: 1
- **Artworks**: 3
- **Concept length**: 97 chars
- **Preface length**: 133 chars
- **No issues detected**

### https://bienal.org.br/agenda/bienal-no-territorio-paulista-arte-contemporanea-e-patrimonio-cultural-sorocaba-sp/
- **Title**: `Bienal no Território Paulista – Arte Contemporânea e Patrimônio Cultural`
- **Dates**: 2026-05-21 → 2026-05-21
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 161 chars
- **Issues**:
  - concept is missing

## reina_sofia (Museo Reina Sofía) — PASS

- URLs found: 9
- URLs tested: 3
- Issues: 0

### https://www.museoreinasofia.es/en/exhibition/alberto-greco
- **Title**: `Viva el arte vivo`
- **Dates**: 2026-02-11 → 2026-06-08
- **Curators**: 1
- **Artworks**: 1
- **Concept length**: 173 chars
- **Preface length**: 198 chars
- **No issues detected**

### https://www.museoreinasofia.es/en/exhibition/andrea-canepa
- **Title**: `Bundle`
- **Dates**: 2026-01-13 → 2027-01-01
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 90 chars
- **Preface length**: 162 chars
- **No issues detected**

### https://www.museoreinasofia.es/en/exhibition/aurelia-munoz
- **Title**: `Aurèlia Muñoz: Beings`
- **Dates**: 2026-04-29 → 2026-09-07
- **Curators**: 3
- **Artworks**: 1
- **Concept length**: 77 chars
- **Preface length**: 141 chars
- **No issues detected**

## sharjah_biennale (Sharjah Biennial) — WARN

- URLs found: 17
- URLs tested: 3
- Issues: 4

### https://www.sharjahart.org/en/sharjah-biennial/sb-1/
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

### https://www.sharjahart.org/en/sharjah-biennial/sb-2/
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

### https://www.sharjahart.org/en/sharjah-biennial/sb-3/
- **Title**: `Sharjah Biennial`
- **Dates**: 1997-04-01 → 1997-04-10
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 0 chars
- **Issues**:
  - concept is missing
  - preface is missing

## sydney_biennale (Sydney Biennale) — WARN

- URLs found: 34
- URLs tested: 3
- Issues: 3

### https://my.biennaleofsydney.art/donate/q/giving-community
- **Title**: `25th Biennale of Sydney`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 89 chars
- **Issues**:
  - concept is missing

### https://www.biennaleofsydney.art/about-us/
- **Title**: `About Us - Biennale of Sydney`
- **Dates**: ? → ?
- **Curators**: 4
- **Artworks**: 8
- **Concept length**: 0 chars
- **Preface length**: 167 chars
- **Issues**:
  - concept is missing

### https://www.biennaleofsydney.art/about-us/#overview
- **Title**: `About Us - Biennale of Sydney`
- **Dates**: ? → ?
- **Curators**: 4
- **Artworks**: 8
- **Concept length**: 0 chars
- **Preface length**: 167 chars
- **Issues**:
  - concept is missing

## taipei_biennale (Taipei Biennial) — WARN

- URLs found: 6
- URLs tested: 3
- Issues: 3

### https://www.tfam.museum/Exhibition/ExhibitionTheme.aspx?ddlLang=zh-tw&id=8&menu=221
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

### https://www.tfam.museum/Exhibition/ExhibitionTheme.aspx?id=11
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

### https://www.tfam.museum/Exhibition/ExhibitionTheme.aspx?id=3
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - content too short after cleaning

## serpentine (Serpentine Galleries) — WARN

- URLs found: 60
- URLs tested: 3
- Issues: 1

### https://www.serpentinegalleries.org/whats-on/364-more-earth-days/
- **Title**: `Brian Eno for 364 More Earth Days`
- **Dates**: 2023-04-23 → 2024-04-21
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 108 chars
- **Preface length**: 222 chars
- **No issues detected**

### https://www.serpentinegalleries.org/whats-on/a-directory-of-public-actions-2/
- **Title**: `A Directory of Public Actions`
- **Dates**: 2016-05-04 → ?
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 190 chars
- **Issues**:
  - concept is missing

### https://www.serpentinegalleries.org/whats-on/act-esol-language-resistance-theatre-resource/
- **Title**: `ACT ESOL: Language, Resistance, Theatre Resource`
- **Dates**: 2019-01-30 → 2019-01-30
- **Curators**: 2
- **Artworks**: 1
- **Concept length**: 169 chars
- **Preface length**: 245 chars
- **No issues detected**

## south_london_gallery (South London Gallery) — WARN

- URLs found: 4
- URLs tested: 3
- Issues: 2

### https://www.southlondongallery.org/exhibitions/paulo-nimer-pjota/
- **Title**: `Paulo Nimer Pjota: Encantados`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 167 chars
- **Issues**:
  - concept is missing

### https://www.southlondongallery.org/exhibitions/ranti-bam-sacred-groves/
- **Title**: `Ranti Bam: SACRED GROVES`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 3
- **Concept length**: 79 chars
- **Preface length**: 141 chars
- **No issues detected**

### https://www.southlondongallery.org/exhibitions/slg-forever-at-christies/
- **Title**: `SLG Forever at Christie's`
- **Dates**: 2026-06-05 → 2026-06-25
- **Curators**: 0
- **Artworks**: 28
- **Concept length**: 0 chars
- **Preface length**: 135 chars
- **Issues**:
  - concept is missing

## tate (Tate Modern) — PASS

- URLs found: 16
- URLs tested: 3
- Issues: 0

### https://www.tate.org.uk/whats-on/tate-modern/ana-mendieta
- **Title**: `Ana Mendieta`
- **Dates**: 2026-07-15 → 2027-01-17
- **Curators**: 1
- **Artworks**: 1
- **Concept length**: 88 chars
- **Preface length**: 230 chars
- **No issues detected**

### https://www.tate.org.uk/whats-on/tate-modern/baya
- **Title**: `Baya`
- **Dates**: 2027-06-10 → 2027-10-17
- **Curators**: 1
- **Artworks**: 1
- **Concept length**: 99 chars
- **Preface length**: 162 chars
- **No issues detected**

### https://www.tate.org.uk/whats-on/tate-modern/edvard-munch
- **Title**: `Edvard Munch`
- **Dates**: 2027-11-11 → 2028-04-23
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 65 chars
- **Preface length**: 122 chars
- **No issues detected**

## venice_biennale (Venice Biennale) — WARN

- URLs found: 16
- URLs tested: 3
- Issues: 3

### https://www.labiennale.org/en/art/2026/accessible-biennale
- **Title**: `Biennale Arte 2026 | The accessible Biennale`
- **Dates**: 2026-05-01 → 2026-11-30
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 134 chars
- **Preface length**: 247 chars
- **No issues detected**

### https://www.labiennale.org/en/art/2026/accreditation
- **Title**: `Biennale Arte 2026`
- **Dates**: 2026-05-09 → 2026-11-22
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 0 chars
- **Issues**:
  - concept is missing
  - preface is missing

### https://www.labiennale.org/en/art/2026/artists
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - LLM returned None

## ucca (UCCA Center for Contemporary Art) — PASS

- URLs found: 28
- URLs tested: 3
- Issues: 0

### https://ucca.org.cn/en/exhibition/a-hollow-in-a-world-too-full/
- **Title**: `Cao Fei: A Hollow in a World Too Full`
- **Dates**: 2018-09-08 → 2018-12-09
- **Curators**: 2
- **Artworks**: 6
- **Concept length**: 81 chars
- **Preface length**: 149 chars
- **No issues detected**

### https://ucca.org.cn/en/exhibition/ad-diriyah-biennale/
- **Title**: `Diriyah Biennale: Feeling the Stones`
- **Dates**: 2021-12-11 → 2022-03-11
- **Curators**: 4
- **Artworks**: 19
- **Concept length**: 117 chars
- **Preface length**: 190 chars
- **No issues detected**

### https://ucca.org.cn/en/exhibition/ahmed-mater-antenna/
- **Title**: `Ahmed Mater: Antenna`
- **Dates**: 2025-03-08 → 2025-06-08
- **Curators**: 1
- **Artworks**: 12
- **Concept length**: 124 chars
- **Preface length**: 193 chars
- **No issues detected**

## yokohama_triennale (Yokohama Triennale) — WARN

- URLs found: 34
- URLs tested: 3
- Issues: 2

### https://www.yokohamatriennale.jp/english/news/8th-yokohama-triennale-official-catalog-digital-english-version-is-now-available-for-free-on-the-official-web-page/
- **Title**: `8th Yokohama Triennale Official Catalog`
- **Dates**: ? → ?
- **Curators**: 2
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 81 chars
- **Issues**:
  - concept is missing

### https://www.yokohamatriennale.jp/english/news/8th-yokohama-triennale-report-is-now-available-online/
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - LLM returned None

### https://www.yokohamatriennale.jp/english/news/8th-yokohama-triennale-wild-grass-our-lives-closes/
- **Title**: `Wild Grass: Our Lives`
- **Dates**: ? → 2024-06-09
- **Curators**: 2
- **Artworks**: 1
- **Concept length**: 106 chars
- **Preface length**: 105 chars
- **No issues detected**

## zkm (ZKM) — WARN

- URLs found: 7
- URLs tested: 3
- Issues: 1

### https://zkm.de/en/exhibition/2018/09/zkmgameplay-the-next-level
- **Title**: `zkm_gameplay. the next level`
- **Dates**: 2018 → ?
- **Curators**: 3
- **Artworks**: 10
- **Concept length**: 103 chars
- **Preface length**: 125 chars
- **Issues**:
  - start_date invalid format (expected YYYY-MM-DD): '2018'

### https://zkm.de/en/exhibition/2024/09/fellow-travellers
- **Title**: `Fellow Travellers`
- **Dates**: 2024-09-21 → 2026-02-08
- **Curators**: 4
- **Artworks**: 3
- **Concept length**: 168 chars
- **Preface length**: 593 chars
- **No issues detected**

### https://zkm.de/en/exhibition/2024/09/you-have-a-new-follower
- **Title**: `You Have a New Follower!`
- **Dates**: ? → 2024-11-22
- **Curators**: 1
- **Artworks**: 6
- **Concept length**: 73 chars
- **Preface length**: 134 chars
- **No issues detected**

## pinakothek (Pinakothek der Moderne) — WARN

- URLs found: 3
- URLs tested: 3
- Issues: 1

### https://www.pinakothek.de/en/ausstellung/reflexion
- **Title**: `Reflexion`
- **Dates**: 2026-02-13 → 2026-05-31
- **Curators**: 7
- **Artworks**: 0
- **Concept length**: 161 chars
- **Preface length**: 198 chars
- **No issues detected**

### https://www.pinakothek.de/en/exhibition/4-museums-1-modernity
- **Title**: `4 Museums – 1 Modernity`
- **Dates**: 2025-04-04 → 2025-09-28
- **Curators**: 0
- **Artworks**: 4
- **Concept length**: 104 chars
- **Preface length**: 153 chars
- **No issues detected**

### https://www.pinakothek.de/en/exhibition/old-masters-on-the-move
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - LLM returned None

## kunsthaus (Kunsthaus Zürich) — WARN

- URLs found: 31
- URLs tested: 3
- Issues: 2

### https://www.kunsthaus.ch/en/besuch-planen/ausstellungen/albert-welti/
- **Title**: `Albert Welti: Imprints of the Fantastic`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 0
- **Concept length**: 0 chars
- **Preface length**: 114 chars
- **Issues**:
  - concept is missing
  - city is missing

### https://www.kunsthaus.ch/en/besuch-planen/ausstellungen/alice-bailly/
- **Title**: `Alice Bailly – Pioneer of Modernism`
- **Dates**: 2025-10-31 → 2026-02-15
- **Curators**: 2
- **Artworks**: 4
- **Concept length**: 93 chars
- **Preface length**: 132 chars
- **No issues detected**

### https://www.kunsthaus.ch/en/besuch-planen/ausstellungen/apropos-hodler/
- **Title**: `Apropos Hodler – Current perspectives on an icon`
- **Dates**: 2024-03-08 → 2024-06-30
- **Curators**: 2
- **Artworks**: 8
- **Concept length**: 125 chars
- **Preface length**: 117 chars
- **No issues detected**

## whitney_biennial (Whitney Biennial) — WARN

- URLs found: 19
- URLs tested: 3
- Issues: 3

### https://whitney.org/exhibitions/12-years-in-azeroth
- **Title**: `Robert Nideffer: 12 Years in Azeroth – The Journey Begins`
- **Dates**: ? → ?
- **Curators**: 0
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 173 chars
- **Issues**:
  - concept is missing

### https://whitney.org/exhibitions/2026-biennial
- **Title**: `N/A`
- **Dates**: ? → ?
- **Curators**: N/A
- **Artworks**: 0
- **Concept length**: N/A chars
- **Preface length**: N/A chars
- **Issues**:
  - LLM returned None

### https://whitney.org/exhibitions/andy-warhol-family-album
- **Title**: `Andy Warhol Family Album`
- **Dates**: 2026-04-30 → 2026-10-19
- **Curators**: 2
- **Artworks**: 1
- **Concept length**: 0 chars
- **Preface length**: 182 chars
- **Issues**:
  - concept is missing

