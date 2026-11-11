# Backfill — standings by season

Run 2026-11-11 14:50 UTC

Competition pages server-render only the standings table; the match list loads client-side. Standings still give played, won, lost, scores for and against and final position per club per competition per season.

- **2023**: nothing returned
- **2024**: nothing returned
- **2025**: nothing returned

## Recon for match-level data

AJAX actions seen on competition pages:


## Sample competition-list payload

```
{"groups":["<option>Select Group<\/option>"],"competition":"        <script>\n            jQuery(\".fix-res-button:eq(0) a\").attr('href','https:\/\/www.galwaygaa.ie\/results?user=6929');\n            jQuery(\".fix-res-button:eq(1) a\").attr('href','https:\/\/www.galwaygaa.ie\/fixtures?user=6929');\n\n        <\/script>\n        <div class=\"competitions-wrap\">\n          <ul class=\"comp-list\">\n                  <li class=\"comp_data\">\n            <div class=\"first-table-item\">\n              <a href=\"https:\/\/www.galwaygaa.ie\/league\/189937\">\n                Connacht GAA Club Senior Football Championship 2023              <\/a>\n            <\/div>\n          <\/li>\n                  <li class=\"comp_data\">\n            <div class=\"first-table-item\">\n              <a href=\"https:\/\/www.galwaygaa.ie\/league\/187995\">\n                Senior Football Championship               <\/a>\n            <\/div>\n          <\/li>\n                  <li class=\"comp_data\">\n            <div class=\"first-table-item\">\n              <a href=\"https:\/\/www.galwaygaa.ie\/league\/188895\">\n                Senior Football Relegation Group              <\/a>\n            <\
```
