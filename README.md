# Norrath Pathfinder

Shortest travel route between any two EverQuest zones, with druid and wizard ports
switched on or off, drawn on a schematic world map and on each zone's real map.

**Live:** https://&lt;user&gt;.github.io/norrath-pathfinder/

## What it does

- Type-to-search pickers for the start and destination zone (87 zones, classic through Velious).
- Toggles for **druid ports**, **wizard ports** and **boats**. A port is cast where you stand,
  so it is modelled as a one-way edge from *any* zone to any ring or spire destination —
  which is why enabling ports usually removes the walking before the port, not after it.
- Dijkstra over the zone graph: a zone line and a port each cost 1 hop, a boat costs 2.
- **World map** with the route drawn across it — straight strokes for zone lines, dashes for
  boats, curved arcs for ports. Click a zone to set the destination, shift-click for the start.
- **Itinerary** collapsing consecutive walks into one line, with the port destination and the
  spell that gets you there (Ring of Feerrott, Teleport: Combine, …) as the headline.
- **Zone by zone** cards, one per zone entered, drawn from that zone's own client map file
  with pins on the real zone-line coordinates. Hover to magnify, click to pin, Esc to close.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The whole site: fonts, geometry and code embedded. No build step, no server, no third-party requests. |
| `build_maps.py` | Regenerates the embedded zone geometry from a local EverQuest client. |

`index.html` already contains the generated geometry, so the site works from a clone as-is.

## Regenerating the zone maps

`build_maps.py` reads the standard EQ map pack (`L` line segments, `P` labelled points) from a
client install, normalises each zone into a 1000-unit box, keeps up to 1200 segments, resolves
every `to_Somewhere` point label to a zone id, and injects the result into `index.html`
between the `<!-- ZONEMAPS -->` markers.

```bash
python build_maps.py
```

Point `MAPS` at the client's `maps` directory first. Two findings worth keeping:

- Map-file coordinates are **already screen-oriented** — do not negate them. Verified twice:
  the pack's own legend text renders upright only under `(x, y)`, and scoring all eight axis
  transforms against 201 zone-pair bearings put `(x, y)` first and `(-x, -y)` last.
- North is therefore not "up" on these drawings. They match the orientation of the in-game
  map, which is what you want when comparing against your screen.

## Editing the travel data

Four tables at the top of the script in `index.html`, one line per entry:

- `ZONES` — `id: [name, region, worldX, worldY]` (world coordinates are the schematic map only)
- `EDGES` — `[a, b]` for a zone line, `[a, b, "boat"]` for a ship
- `DRUID` / `WIZARD` — `zone: "Spell Name"` for each port destination

The graph is a reconstruction of classic/Kunark/Velious connectivity; correct anything your
server does differently and reload.

## Hosting

Static, single file. GitHub Pages: Settings → Pages → Source `main` / root.

## Privacy

The page makes **no third-party requests**. Cinzel, Alegreya Sans and JetBrains Mono
(SIL Open Font License 1.1, latin subsets) are embedded as base64 WOFF2 rather than
hotlinked from Google Fonts, which is what a German court found to breach GDPR in
LG München I, 3 O 17493/20 — the fonts are freely licensed, but the hotlink hands the
visitor's IP address to a third party. There are no cookies, no analytics, no storage,
and no user input leaves the browser. The host's own server logs (GitHub's, here) still
record visitor IPs, as every web server does.

## Data provenance

Zone geometry is derived from **Brewall's EverQuest maps** (pack `brewall-20240109`) by
Brewall Rainsinger, with a number of zones revised by Goodurden. The pack is distributed free
for player use at [eqmaps.info](https://www.eqmaps.info/); this project embeds a simplified
trace of it (up to 1200 line segments per zone) and credits it in the page footer. It carries
no formal licence, so treat continued use as courtesy: keep the credit, and take it down if
the author asks.

EverQuest is a trademark of Daybreak Game Company. This project is unaffiliated with Daybreak
or with the map authors.
