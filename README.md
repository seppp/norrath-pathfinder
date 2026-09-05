# Norrath Pathfinder

Shortest travel route between any two EverQuest zones, with druid and wizard ports
switched on or off, drawn on a schematic world map and on each zone's real map.

**Live:** https://seppp.github.io/norrath-pathfinder

## What it does

- Type-to-search pickers for the start and destination zone (118 zones — outdoor zones, city
  districts and the dungeons hanging off them).
- **Expansion toggles.** Classic is always on; Ruins of Kunark and Scars of Velious can each be
  switched off, which removes those zones from the map, the pickers and the search — a server
  running classic only cannot route through Kunark. Defaults to classic alone (75 zones);
  all three gives 118. A zone's expansion follows its continent, since everything on Kunark
  and Velious arrived with its own expansion. Selecting a zone and then switching its
  expansion off moves the selection to one that still exists.
- Toggles for **druid ports**, **wizard ports** and **boats**. A port is cast where you stand,
  so it is modelled as a one-way edge from *any* zone to any ring or spire destination —
  which is why enabling ports usually removes the walking before the port, not after it.
- Dijkstra over the zone graph — see [How routing works](#how-routing-works).
- **Several stops at once**, each toggleable, visited in whatever order is shortest. Exact up
  to twelve stops (Held-Karp over subsets), nearest-neighbour plus 2-opt beyond, with an
  optional return to the start. The stop list **is** the itinerary: a stop
  can be moved with the arrows, which locks it to that position, and the unlocked stops are
  dealt into whichever gaps are left, cheapest first. A quest whose turn-ins must happen in
  sequence simply locks them. Solved exactly while twelve or fewer stops are unlocked (a
  layered subset walk over the free ones, one layer per position), greedy beyond. Picking a quest from the selector beside the theme toggle fills in its stops:
  the Coin of Tash gives ten coin cities plus a locked four-step turn-in chain, and its ten
  coins alone are 120 zone lines in the order the guides list them, 66 in the best order on foot.
  A stop can carry a `/loc` and a hint, drawn as a marker on that zone's own map — wiki `/loc`
  is `(Y, X)` and the map files hold its negation, verified against two quest NPCs (Mizr N'Mar,
  Romar Sunto) that appear in both coordinate systems.
- **World map** with the route drawn across it — straight strokes for zone lines, dashes for
  boats, curved arcs for ports. Click a zone to set the destination, shift-click for the start.
- **Itinerary** collapsing consecutive walks into one line, with the port destination and the
  spell that gets you there (Ring of Feerrott, Teleport: Combine, …) as the headline.
- **Zone by zone** cards, one per zone entered, drawn from that zone's own client map file
  with pins on the real zone-line coordinates. Hover to magnify, click to pin, Esc to close.

## How routing works

Dijkstra over a graph rebuilt on every change — the toggles change the *graph*, not the search.

```js
const COST = {walk:1, boat:2, druid:1, wizard:1};
```

A zone line and a port each cost 1 hop; a boat costs 2, because you wait on the dock for it.
The unequal weights are why this is Dijkstra and not a breadth-first search: BFS would offer
you a two-boat crossing over a three-zone walk. With 114 zones the frontier is a linear scan
rather than a heap. The search stops when the destination is the cheapest unfinalised zone,
which is what makes the answer optimal rather than merely plausible.

**Ties are common** — ports cost 1 from anywhere, so "port to ring A, walk twice" and
"port to ring B, walk twice" score the same all over Norrath. Two strict `<` comparisons
settle them:

- the frontier scan takes the first zone of equal cost in `dist` insertion order;
- relaxation (`d < dist[e.to]`) keeps the first equally-cheap predecessor and never
  overwrites it with a later one.

Insertion order follows how the graph is built — `EDGES` in declaration order, then druid
port edges, then wizard. So the result is **deterministic** (same start, destination and
toggles always produce the same route), and an exact druid/wizard tie resolves to **druid**,
purely because those edges are added first. Nothing judged it better.

"Shortest" therefore means *fewest weighted hops*, and among equally short routes you get an
arbitrary-but-stable pick, not a considered one.

**Not modelled:** how long a zone takes to cross. Every zone line costs the same, so Ak'Anon
and the Eastern Wastes are both one hop, and a route may enter a zone at one corner and leave
by the far one — zone size, terrain, run speed and the distance between the two zone lines
carry no weight. Fewest zone lines is not always quickest on foot. Nor are boat schedules,
danger, level, or faction. A ring in the Great Divide is as cheap as
one in the Commonlands. Any of these could become a preference — weight zones by crossing
time, penalise ports, avoid a named zone — by changing the cost table and the edge weights.

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

Port destinations and spell names come from the Legends ritual table
([eqlwiki.com/Rituals](https://eqlwiki.com/Rituals), as of 2026-06-20), not live EQ — they
differ. Druids get Rings (self) and Circles (group) to eleven zones plus Succor: East Karana;
wizards get Gates (self) and Portals (group) to nine zones, plus Evacuate: South Ro and the
two Alter Plane rituals. The Planes of Hate and Sky have no zone lines at all: a wizard ritual
is the only way in and Gate the only way out, so with wizard ports off they are unreachable —
which the search reports rather than inventing a walk. The Plane of Fear is reached on foot,
through the portal in the Feerrott, modelled as an edge of type `portal`: one-way, since you
cannot walk back out. `["feerrott","fear","portal"]` in `EDGES` is the whole of it. The page
names the group version, since it is the one you ask a porter for. Kunark and Velious have no
rituals in Legends, so those destinations keep live EQ names and only appear when you switch
those expansions on.

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
