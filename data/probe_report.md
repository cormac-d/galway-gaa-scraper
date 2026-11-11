# Competition id probe

Run 2026-11-11 14:24 UTC

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

## 2. Id probe via 

Probing 29 ids.

| id | status | years | title |
|---|---|---|---|
| 217984 | error: MissingSchema | - | - |
| 217852 | error: MissingSchema | - | - |
| 217522 | error: MissingSchema | - | - |
| 217009 | error: MissingSchema | - | - |
| 215416 | error: MissingSchema | - | - |
| 215383 | error: MissingSchema | - | - |
| 215277 | error: MissingSchema | - | - |
| 214631 | error: MissingSchema | - | - |
| 214414 | error: MissingSchema | - | - |
| 213914 | error: MissingSchema | - | - |
| 213774 | error: MissingSchema | - | - |
| 213414 | error: MissingSchema | - | - |
| 212414 | error: MissingSchema | - | - |
| 212156 | error: MissingSchema | - | - |
| 211414 | error: MissingSchema | - | - |
| 209414 | error: MissingSchema | - | - |
| 207454 | error: MissingSchema | - | - |
| 206914 | error: MissingSchema | - | - |
| 204414 | error: MissingSchema | - | - |
| 199414 | error: MissingSchema | - | - |
| 194414 | error: MissingSchema | - | - |
| 189414 | error: MissingSchema | - | - |
| 184414 | error: MissingSchema | - | - |
| 178823 | error: MissingSchema | - | - |
| 174414 | error: MissingSchema | - | - |
| 164414 | error: MissingSchema | - | - |
| 149414 | error: MissingSchema | - | - |
| 134414 | error: MissingSchema | - | - |
| 114414 | error: MissingSchema | - | - |

## 3. Which ids carry which season

No dated competitions found - the pages may be JavaScript-rendered, in which case this needs the playwright approach used by scraper.py.

