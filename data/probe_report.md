# Competition id probe

Run 2026-11-11 14:27 UTC

## 1. Discovery on index pages

- https://www.galwaygaa.ie/fixtures-results/ -> http 404
- https://www.galwaygaa.ie/fixtures-and-results/ -> http 404
- https://www.galwaygaa.ie/results/ -> ok, 18 league ids, 0 season selector(s)
-     id range 218899-220513 (sample [218899, 218902, 219090, 219091, 219439, 219440, 219441, 219555])
- https://www.galwaygaa.ie/competitions/ -> ok, 209 league ids, 0 season selector(s)
-     id range 178819-190295 (sample [178819, 178820, 178821, 178822, 178823, 178875, 178886, 178887])
- https://mayogaa.com/fixtures-results/ -> ok, 0 league ids, 0 season selector(s)
- https://mayogaa.com/fixtures-and-results/ -> http 404
- https://mayogaa.com/results/ -> ok, 5 league ids, 0 season selector(s)
-     id range 220232-220977 (sample [220232, 220236, 220237, 220832, 220977])
- https://mayogaa.com/competitions/ -> ok, 385 league ids, 0 season selector(s)
-     id range 212145-220978 (sample [212145, 212152, 212153, 212154, 212155, 212156, 212157, 212158])
- https://gaacork.ie/fixtures-results/ -> ok, 58 league ids, 0 season selector(s)
-     id range 211619-218835 (sample [211619, 211620, 211621, 211622, 211623, 211624, 211625, 211713])
- https://gaacork.ie/fixtures-and-results/ -> http 404
- https://gaacork.ie/results/ -> ok, 33 league ids, 0 season selector(s)
-     id range 211619-216010 (sample [211619, 211620, 211621, 211622, 211623, 211624, 211625, 211713])
- https://gaacork.ie/competitions/ -> ok, 53 league ids, 0 season selector(s)
-     id range 207451-216008 (sample [207451, 207452, 207454, 207455, 207458, 207460, 207470, 207473])

Discovered 692 ids, range 178819-220978.

## 2. Id probe via https://mayogaa.com

Probing 47 ids.

| id | status | years | title | index label |
|---|---|---|---|---|
| 220978 | ok | 2023,2024,2025,2026 | League | McHale Agri Forest Garden Under 21 Football B - Kn |
| 220231 | ok | 2023,2024,2025,2026 | League | Michael Walsh Cup  Division 1 - Cup Division 1 |
| 219555 | ok | 2023,2024,2025,2026 | League | FBD Under 16  - Group 2 |
| 219439 | ok | 2023,2024,2025,2026 | League | U19 C Football Championship |
| 219191 | ok | 2023,2024,2025,2026 | League | Homeland U15 Autumn League - League Division 4 |
| 219160 | ok | 2023,2024,2025,2026 | League | Homeland U13 Autumn Leagues - Cup Division 5 |
| 219143 | ok | 2023,2024,2025,2026 | League | Homeland U13 Development Autumn League - League Di |
| 218822 | ok | 2023,2024,2025,2026 | League | Homeland U14 Hurling Championship - Group 2 |
| 217850 | ok | 2023,2024,2025,2026 | League | Senior C Hurling |
| 217524 | ok | 2023,2024,2025,2026 | League | Connacht Gold Senior Club Championship - Group 3 |
| 217175 | ok | 2023,2024,2025,2026 | League | Homeland Mayo GAA U16 C Championship Shield Finals |
| 217158 | ok | 2023,2024,2025,2026 | League | Homeland Mayo GAA U14 C Championship Shield Finals |
| 217141 | ok | 2023,2024,2025,2026 | League | Homeland Mayo GAA Minor D Championship 2026 - Grou |
| 217124 | ok | 2023,2024,2025,2026 | League | Homeland Mayo GAA U14 F Championship 2026 - Group  |
| 216696 | ok | 2023,2024,2025,2026 | League | The Junction Restaurant North Mayo Minor D Champio |
| 216405 | ok | 2023,2024,2025,2026 | League | St Colman's Credit Union South Mayo U16 - Cup Divi |
| 216298 | ok | 2023,2024,2025,2026 | League | West Mayo U16 Championship - Cup Division 2 |
| 216055 | ok | 2023,2024,2025,2026 | League | Homeland U14 Leagues 2026 - Cup Division 2 |
| 215987 | ok | 2009,2014,2018,2021,2023,2024,2025,2026 | League | Senior ‘A’ |
| 215425 | ok | 2023,2024,2025,2026 | League | John West Feile Peil na nOg Maigheo Division 3 - C |
| 215416 | ok | 2023,2024,2025,2026 | League | John West Feile Peil na nOg Maigheo - League Divis |
| 215383 | ok | 2023,2024,2025,2026 | League | John West Feile Peil na nOg Maigheo Division 2 - C |
| 215277 | ok | 2023,2024,2025,2026 | League | - |
| 215227 | ok | 2023,2024,2025,2026 | League | Premier Junior B Championship  - Group 3 |
| 215027 | ok | 2023,2024,2025,2026 | League | Homeland U12 Spring League 2026 - 2 Team Group 2 |
| 214931 | ok | 2023,2024,2025,2026 | League | Abbvie Mayo Senior League Division 4 |
| 214631 | ok | 2023,2024,2025,2026 | League | - |
| 214571 | ok | 2023,2024,2025,2026 | League | North Mayo Sweeney Cup Senior and Intermediate Fin |
| 214414 | ok | 2023,2024,2025,2026 | League | - |
| 213938 | ok | 2023,2024,2025,2026 | League | Junior Hurling Championship - Group 2 |
| 213767 | ok | 2023,2024,2025,2026 | League | Homeland U14 Leagues 2026 - League Division 3 |
| 212162 | ok | 2023,2024,2025,2026 | League | PPS Juvenile B Football Competition 2025/26- Group |
| 211714 | ok | 2023,2024,2025,2026 | League | Division 2 HL |
| 207508 | ok | 2023,2024,2025,2026 | League | Link to View Competition |
| 189956 | ok | 2023,2024,2025,2026 | League | - |
| 188338 | ok | 2023,2024,2025,2026 | League | - |
| 187824 | ok | 2023,2024,2025,2026 | League | - |
| 186045 | ok | 2023,2024,2025,2026 | League | - |
| 185183 | ok | 2023,2024,2025,2026 | League | - |
| 184272 | ok | 2023,2024,2025,2026 | League | - |
| 183667 | ok | 2023,2024,2025,2026 | League | - |
| 183226 | ok | 2023,2024,2025,2026 | League | - |
| 181881 | ok | 2023,2024,2025,2026 | League | - |
| 180979 | ok | 2023,2024,2025,2026 | League | - |
| 180483 | ok | 2023,2024,2025,2026 | League | - |
| 180000 | ok | 2023,2024,2025,2026 | League | - |
| 178819 | ok | 2023,2024,2025,2026 | League | - |

## 3. Which ids carry which season

- **2026**: 47 ids, 178819-220978
- **2025**: 47 ids, 178819-220978
- **2024**: 47 ids, 178819-220978
- **2023**: 47 ids, 178819-220978
- **2021**: 1 ids, 215987-215987
- **2018**: 1 ids, 215987-215987
- **2014**: 1 ids, 215987-215987
- **2009**: 1 ids, 215987-215987

