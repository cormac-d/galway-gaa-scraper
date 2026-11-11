# Season enumeration

Run 2026-11-11 14:31 UTC

The results page has no season control, only fdate/tdate, which is why date-chunking earlier years returned nothing. The competitions page drives a `seasonid` parameter through admin-ajax.php instead. This sweeps that parameter for football (value=6929).

## Seasons returning football competitions: 4

| seasonid | competitions | id range | sample names |
|---|---|---|---|
| 3070 | 209 | 178819-190295 |  |
| 3642 | 343 | 193100-204547 |  |
| 3831 | 262 | 201764-212024 |  |
| 3976 | 205 | 214396-220513 |  |

## Dating each season from real match dates

| seasonid | competition sampled | match years | title |
|---|---|---|---|
| 3070 | 178819 | 2023 | Cahill Cup - Group 3 |
| 3642 | 193100 | 2024 | Division 3B Football League |
| 3831 | 201764 | 2025 | Division 2 Football League |
| 3976 | 214396 | 2026 | U19 A West Football League |

## Verdict

- seasonid **3070** -> 2023
- seasonid **3642** -> 2024
- seasonid **3831** -> 2025
- seasonid **3976** -> 2026

To backfill, the scraper should request competitions for the wanted seasonid, then read each competition page by id, rather than driving fdate/tdate on the results page.
