"""Convert EQ client map files into compact per-zone geometry for the pathfinder page.

Reads the standard map pack (L = line segments, P = labelled points) and emits
ZONEMAPS as JavaScript: normalised outlines plus the real coordinates of each
zone line, keyed by the zone it leads to.
"""
import json, math, os, re, sys

MAPS = r"C:\eqemu\everquest_rof2\everquest_rof2\maps"
OUT  = r"C:\Users\sigha\OneDrive\Documents\EQLTravel\zonemaps.js"

MAX_SEGMENTS = 1200          # per zone, longest kept
BOX = 1000.0                # normalised width

# zone id -> candidate map basenames (first that exists wins)
FILES = {
 "qeynos_s":["qeynos"], "qeynos_n":["qeynos2"], "qeynos_hills":["qeytoqrg"],
 "surefall":["qrg"], "blackburrow":["blackburrow"], "everfrost":["everfrost"],
 "halas":["halas"], "permafrost":["permafrost"], "wkarana":["qey2hh1"],
 "nkarana":["northkarana"], "skarana":["southkarana"], "ekarana":["eastkarana"],
 "highpass":["highpass"], "highkeep":["highkeep"], "gorge":["beholder"],
 "runnyeye":["runnyeye"], "kithicor":["kithicor"], "rivervale":["rivervale"],
 "misty":["misty","mistythicket"], "ecommons":["ecommons"], "wcommons":["commons"],
 "befallen":["befallen"], "wfreeport":["freportw"], "nfreeport":["freportn"],
 "efreeport":["freporte"], "nro":["nro"], "sro":["sro"], "oasis":["oasis"],
 "innothule":["innothule"], "grobb":["grobb"], "guk":["guktop"],
 "feerrott":["feerrott"], "cazic":["cazicthule"], "rathe":["rathemtn"],
 "lakerathe":["lakerathe"], "nektulos":["nektulos"], "neriak":["neriaka"],
 "lavastorm":["lavastorm"], "najena":["najena"], "soleye":["soldunga"],
 "ocean":["oot"], "erudsxing":["erudsxing"], "kerra":["kerraridge"],
 "erudin":["erudnext"], "erudin_palace":["erudnint"], "toxxulia":["tox"],
 "paineel":["paineel"], "butcherblock":["butcher"], "kaladim":["kaladima"],
 "cauldron":["cauldron"], "unrest":["unrest"], "gfay":["gfaydark"],
 "felwithe":["felwithea"], "crushbone":["crushbone"], "lfay":["lfaydark"],
 "mistmoore":["mistmoore"], "steamfont":["steamfont"], "akanon":["akanon"],
 "timorous":["timorous"], "fv":["firiona"], "loio":["lakeofillomen"],
 "warslik":["warslikswood","warslikswoods"], "cabilis":["cabeast"], "fob":["fieldofbone"],
 "kurn":["kurn"], "swamp":["swampofnohope"], "frontier":["frontiermtns"],
 "dreadlands":["dreadlands"], "karnor":["karnor"], "burning":["burningwood"],
 "skyfire":["skyfire"], "emerald":["emeraldjungle"], "trakanon":["trakanon"],
 "sebilis":["sebilis"], "overthere":["overthere"], "chardok":["chardok"],
 "iceclad":["iceclad"], "tofs":["frozenshadow"], "ewastes":["eastwastes"],
 "gdivide":["greatdivide"], "thurgadin":["thurgadina"], "kael":["kael"],
 "wakening":["wakening"], "wwastes":["westwastes"], "skyshrine":["skyshrine"],
 "cobalt":["cobaltscar"], "siren":["sirens"],
 # city interiors, dungeons and outposts
 "qcat":["qcat"], "oggok":["oggok"], "gukbottom":["gukbottom"], "paw":["paw"],
 "soldungb":["soldungb"], "soltemple":["soltemple"], "neriakb":["neriakb"],
 "neriakc":["neriakc"], "kaladimb":["kaladimb"], "felwitheb":["felwitheb"],
 "kedge":["kedge"], "hole":["hole"], "warrens":["warrens"], "cabwest":["cabwest"],
 "kaesora":["kaesora"], "dalnir":["dalnir"], "nurga":["nurga"], "droga":["droga"],
 "citymist":["citymist"], "charasis":["charasis"], "veeshan":["veeshan"],
 "crystal":["crystal"], "velketor":["velketor"], "templeveeshan":["templeveeshan"],
 "necropolis":["necropolis"], "sleeper":["sleeper"], "icewell":["thurgadinb"],
}

# zone id -> the display name, for matching "to_..." labels
NAMES = {
 "qeynos_s":"South Qeynos","qeynos_n":"North Qeynos","qeynos_hills":"Qeynos Hills",
 "surefall":"Surefall Glade","blackburrow":"Blackburrow","everfrost":"Everfrost Peaks",
 "halas":"Halas","permafrost":"Permafrost Caverns","wkarana":"West Karana",
 "nkarana":"North Karana","skarana":"South Karana","ekarana":"East Karana",
 "highpass":"Highpass Hold","highkeep":"High Keep","gorge":"Gorge of King Xorbb",
 "runnyeye":"Runnyeye Citadel","kithicor":"Kithicor Forest","rivervale":"Rivervale",
 "misty":"Misty Thicket","ecommons":"East Commonlands","wcommons":"West Commonlands",
 "befallen":"Befallen","wfreeport":"West Freeport","nfreeport":"North Freeport",
 "efreeport":"East Freeport","nro":"Northern Desert of Ro","sro":"Southern Desert of Ro",
 "oasis":"Oasis of Marr","innothule":"Innothule Swamp","grobb":"Grobb","guk":"Upper Guk",
 "feerrott":"The Feerrott","cazic":"Cazic-Thule","rathe":"Rathe Mountains",
 "lakerathe":"Lake Rathetear","nektulos":"Nektulos Forest","neriak":"Neriak Foreign Quarter",
 "lavastorm":"Lavastorm Mountains","najena":"Najena","soleye":"Solusek's Eye",
 "ocean":"Ocean of Tears","erudsxing":"Erud's Crossing","kerra":"Kerra Isle",
 "erudin":"Erudin","erudin_palace":"Erudin Palace","toxxulia":"Toxxulia Forest",
 "paineel":"Paineel","butcherblock":"Butcherblock Mountains","kaladim":"Kaladim",
 "cauldron":"Dagnor's Cauldron","unrest":"Estate of Unrest","gfay":"Greater Faydark",
 "felwithe":"Northern Felwithe","crushbone":"Clan Crushbone","lfay":"Lesser Faydark",
 "mistmoore":"Castle Mistmoore","steamfont":"Steamfont Mountains","akanon":"Ak'Anon",
 "timorous":"Timorous Deep","fv":"Firiona Vie","loio":"Lake of Ill Omen",
 "warslik":"Warsliks Woods","cabilis":"Cabilis","fob":"Field of Bone",
 "kurn":"Kurn's Tower","swamp":"Swamp of No Hope","frontier":"Frontier Mountains",
 "dreadlands":"The Dreadlands","karnor":"Karnor's Castle","burning":"Burning Woods",
 "skyfire":"Skyfire Mountains","emerald":"Emerald Jungle","trakanon":"Trakanon's Teeth",
 "sebilis":"Old Sebilis","overthere":"The Overthere","chardok":"Chardok",
 "iceclad":"Iceclad Ocean","tofs":"Tower of Frozen Shadow","ewastes":"Eastern Wastes",
 "gdivide":"Great Divide","thurgadin":"Thurgadin","kael":"Kael Drakkel",
 "wakening":"The Wakening Land","wwastes":"Western Wastes","skyshrine":"Skyshrine",
 "cobalt":"Cobalt Scar","siren":"Siren's Grotto",
 "qcat":"Qeynos Catacombs","oggok":"Oggok","gukbottom":"Lower Guk",
 "paw":"Lair of the Splitpaw","soldungb":"Nagafen's Lair",
 "soltemple":"Temple of Solusek Ro","neriakb":"Neriak Commons",
 "neriakc":"Neriak Third Gate","kaladimb":"South Kaladim",
 "felwitheb":"Southern Felwithe","kedge":"Kedge Keep","hole":"The Hole",
 "warrens":"The Warrens","cabwest":"Cabilis West","kaesora":"Kaesora",
 "dalnir":"Crypt of Dalnir","nurga":"Mines of Nurga","droga":"Temple of Droga",
 "citymist":"City of Mist","charasis":"Howling Stones","veeshan":"Veeshan's Peak",
 "crystal":"Crystal Caverns","velketor":"Velketor's Labyrinth",
 "templeveeshan":"Temple of Veeshan","necropolis":"Dragon Necropolis",
 "sleeper":"Sleeper's Tomb","icewell":"Icewell Keep",
}

# extra spellings the map labels use
ALIASES = {
 "feerrott":["feerott","the feerott","feerrott"],
 "butcherblock":["butcherblock mountains","butcher block","butcherblock"],
 "guk":["the city of guk","upper guk","guk"],
 "cazic":["cazic thule","lost temple of cazic thule","temple of cazic thule","cazic-thule"],
 "innothule":["innothule swamp","innothule"],
 "wcommons":["west commonlands","the commonlands","commonlands","west commons"],
 "ecommons":["east commonlands","east commons"],
 "nro":["north desert of ro","northern desert of ro","north ro"],
 "sro":["south desert of ro","southern desert of ro","south ro"],
 "oasis":["oasis of marr","the oasis of marr","oasis"],
 "neriak":["neriak","neriak foreign quarter","foreign quarter"],
 "soleye":["soluseks eye","solusek s eye","solusek's eye","soleye"],
 "ocean":["ocean of tears","the ocean of tears"],
 "erudsxing":["eruds crossing","erud s crossing","erud's crossing"],
 "kerra":["kerra isle","kerra ridge","kerra island"],
 "erudin":["erudin"], "erudin_palace":["erudin palace"],
 "toxxulia":["toxxulia forest","toxxulia","tox forest"],
 "gfay":["greater faydark"], "lfay":["lesser faydark"],
 "felwithe":["northern felwithe","north felwithe","felwithe"],
 "kaladim":["kaladim","north kaladim","kaladim north"],
 "cauldron":["dagnors cauldron","dagnor s cauldron","dagnor's cauldron"],
 "unrest":["estate of unrest","the estate of unrest","unrest"],
 "mistmoore":["castle mistmoore","mistmoore"],
 "crushbone":["clan crushbone","crushbone"],
 "steamfont":["steamfont mountains","steamfont"],
 "akanon":["ak anon","akanon","ak'anon"],
 "misty":["misty thicket"], "runnyeye":["runnyeye citadel","runnyeye"],
 "gorge":["gorge of king xorbb","beholder","the gorge of king xorbb"],
 "highpass":["highpass hold","high pass hold","highpass"],
 "highkeep":["high keep","highkeep"],
 "kithicor":["kithicor forest","kithicor woods","kithicor"],
 "qeynos_s":["south qeynos","qeynos"], "qeynos_n":["north qeynos"],
 "qeynos_hills":["qeynos hills","the qeynos hills"],
 "surefall":["surefall glade","surefall"],
 "wkarana":["west karana","western karana","the western plains of karana"],
 "nkarana":["north karana","northern karana","the northern plains of karana"],
 "skarana":["south karana","southern karana","the southern plains of karana"],
 "ekarana":["east karana","eastern karana","the eastern plains of karana"],
 "everfrost":["everfrost peaks","everfrost"],
 "permafrost":["permafrost caverns","permafrost keep","permafrost"],
 "halas":["halas","the city of halas"],
 "wfreeport":["west freeport","freeport west"],
 "nfreeport":["north freeport","freeport north"],
 "efreeport":["east freeport","freeport east"],
 "rathe":["rathe mountains","the rathe mountains","rathe"],
 "lakerathe":["lake rathetear","lake rathe"],
 "nektulos":["nektulos forest","the nektulos forest"],
 "lavastorm":["lavastorm mountains","lavastorm"],
 "najena":["najena"], "befallen":["befallen"],
 "fv":["firiona vie","firiona"], "loio":["lake of ill omen","the lake of ill omen"],
 "warslik":["warsliks woods","warslik s woods","warslik woods"],
 "cabilis":["cabilis","cabilis east","east cabilis"],
 "fob":["field of bone","the field of bone"],
 "kurn":["kurns tower","kurn s tower","kurn's tower"],
 "swamp":["swamp of no hope","the swamp of no hope"],
 "frontier":["frontier mountains","the frontier mountains"],
 "dreadlands":["the dreadlands","dreadlands"],
 "karnor":["karnors castle","karnor s castle","karnor's castle"],
 "burning":["burning woods","the burning woods"],
 "skyfire":["skyfire mountains","the skyfire mountains"],
 "emerald":["emerald jungle","the emerald jungle"],
 "trakanon":["trakanons teeth","trakanon s teeth","trakanon's teeth"],
 "sebilis":["old sebilis","sebilis","ruins of sebilis"],
 "overthere":["the overthere","overthere"], "chardok":["chardok"],
 "timorous":["timorous deep","the timorous deep"],
 "iceclad":["iceclad ocean","the iceclad ocean","iceclad"],
 "tofs":["tower of frozen shadow","the tower of frozen shadow"],
 "ewastes":["eastern wastes","the eastern wastes"],
 "wwastes":["western wastes","the western wastes"],
 "gdivide":["great divide","the great divide"],
 "thurgadin":["thurgadin","city of thurgadin"],
 "kael":["kael drakkel","kael"],
 "wakening":["the wakening land","wakening land","wakening lands"],
 "skyshrine":["skyshrine"], "cobalt":["cobalt scar","the cobalt scar"],
 "siren":["sirens grotto","siren s grotto","siren's grotto"],
 "paineel":["paineel"], "blackburrow":["blackburrow"],
 "rivervale":["rivervale"], "grobb":["grobb"],
 # spellings, typos and old/new names the map labels use
 "mistmoore":["castle mistmoore","the castle of mistmoore","castle of mistmoore"],
 "runnyeye":["runnyeye citadel","liberated citadel of runnyeye","runnyeye"],
 "toxxulia":["toxxulia forest","toxullia forest","toxxulia","tox forest"],
 "nektulos":["nektulos forest","nektulos forrest"],
 "gorge":["gorge of king xorbb","valley of king xorbb","beholder"],
 "guk":["the city of guk","city of guk","upper guk","guk"],
 "gukbottom":["ruins of old guk","lower guk","old guk"],
 "qcat":["qeynos aqueduct system","qeynos aquaduct system","qeynos catacombs","aqueducts"],
 "oggok":["oggok","city of oggok"],
 "paw":["lair of the splitpaw","splitpaw","the lair of the splitpaw"],
 "soldungb":["nagafen s lair","nagafens lair","lavastorm caverns"],
 "soltemple":["temple of solusek ro","solusek ro temple"],
 "neriakb":["neriak commons","neriak the commons"],
 "neriakc":["neriak third gate","neriak 3rd gate","third gate"],
 "kaladimb":["south kaladim","kaladim south"],
 "felwitheb":["southern felwithe","south felwithe"],
 "kedge":["kedge keep","the kedge keep"],
 "hole":["ruins of old paineel","the hole","hole"],
 "warrens":["the warrens","warrens"],
 "cabwest":["cabilis west","cablis west","west cabilis"],
 "kaesora":["kaesora","old kaesora"],
 "dalnir":["crypt of dalnir","the crypt of dalnir","dalnir"],
 "nurga":["mines of nurga","the mines of nurga","nurga"],
 "droga":["temple of droga","the temple of droga","droga"],
 "citymist":["city of mist","the city of mist"],
 "charasis":["howling stones","the howling stones","charasis"],
 "veeshan":["veeshan s peak","veeshans peak"],
 "crystal":["crystal caverns","the crystal caverns"],
 "velketor":["velketor s labyrinth","velketors labyrinth","velketor"],
 "templeveeshan":["temple of veeshan","the temple of veeshan"],
 "necropolis":["dragon necropolis","the dragon necropolis"],
 "sleeper":["sleeper s tomb","the sleeper s tomb","sleepers tomb"],
 "icewell":["icewell keep","the icewell keep"],
}

def norm(s):
    s = s.lower().replace("_"," ").replace("-"," ").replace("'"," ")
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s.startswith("the "): s = s[4:]
    return s

LOOKUP = {}
for zid, nm in NAMES.items():
    for cand in [norm(nm)] + [norm(a) for a in ALIASES.get(zid, [])]:
        LOOKUP.setdefault(cand, zid)

def resolve(label):
    """Map a 'to_Xxx' point label onto a zone id, or None."""
    s = norm(label)
    if s.startswith("to "): s = norm(s[3:])
    if s in LOOKUP: return LOOKUP[s]
    for key, zid in LOOKUP.items():                  # tolerate extra words
        if key and (s.startswith(key) or key.startswith(s)) and abs(len(key)-len(s)) <= 6:
            return zid
    return None

PORT_RE = re.compile(r"druid.?ring|^ring|wizard|spire|teleport|portal", re.I)

def read_zone(base):
    """Return (segments, points) from base.txt plus its _1/_2 overlays."""
    segs, pts = [], []
    for suffix in ("", "_1", "_2", "_3"):
        path = os.path.join(MAPS, base + suffix + ".txt")
        if not os.path.exists(path): continue
        with open(path, "r", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("L "):
                    f = line[2:].split(",")
                    if len(f) < 6: continue
                    try: segs.append(tuple(float(f[i]) for i in (0,1,3,4)))
                    except ValueError: pass
                elif line.startswith("P "):
                    f = line[2:].split(",")
                    if len(f) < 8: continue
                    try: x, y = float(f[0]), float(f[1])
                    except ValueError: continue
                    pts.append((x, y, f[7].strip()))
    return segs, pts

def build(zid, base):
    segs, pts = read_zone(base)
    if not segs: return None, "no line data"

    # Map-file coords are already screen-oriented (verified against the packs'
    # own legend text and against zone-line bearings across 200 zone pairs).

    xs = [v for s in segs for v in (s[0], s[2])]
    ys = [v for s in segs for v in (s[1], s[3])]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = max(maxx-minx, 1e-6), max(maxy-miny, 1e-6)
    scale = BOX / max(w, h)
    ox = (BOX - w*scale)/2 - minx*scale
    oy = (BOX - h*scale)/2 - miny*scale
    tx = lambda x: round(x*scale + ox)
    ty = lambda y: round(y*scale + oy)

    # keep the longest segments: they carry the zone's shape
    segs.sort(key=lambda s: (s[0]-s[2])**2 + (s[1]-s[3])**2, reverse=True)
    flat, seen = [], set()
    for a, b, c, d in segs[:MAX_SEGMENTS*3]:
        q = (tx(a), ty(b), tx(c), ty(d))
        if q[0] == q[2] and q[1] == q[3]: continue
        if q in seen: continue
        seen.add(q)
        flat.extend(q)
        if len(flat) >= MAX_SEGMENTS*4: break

    links, ports, unresolved = {}, [], []
    for x, y, lbl in pts:
        if lbl.lower().startswith("to_"):
            target = resolve(lbl)
            if target and target != zid and target not in links: links[target] = [tx(x), ty(y)]
            elif not target: unresolved.append(lbl)
        elif PORT_RE.search(lbl) and not ports:
            ports = [tx(x), ty(y)]

    zone = {"seg": flat, "links": links}
    if ports: zone["port"] = ports
    return zone, unresolved

def main():
    out, report = {}, []
    for zid, cands in FILES.items():
        base = next((c for c in cands if os.path.exists(os.path.join(MAPS, c + ".txt"))), None)
        if not base:
            report.append((zid, "NO MAP FILE", cands)); continue
        zone, extra = build(zid, base)
        if zone is None:
            report.append((zid, extra, base)); continue
        out[zid] = zone
        report.append((zid, "ok: %d segs, %d links" % (len(zone["seg"])//4, len(zone["links"])), base))

    with open(OUT, "w") as fh:
        fh.write("const ZONEMAPS = " + json.dumps(out, separators=(",", ":")) + ";\n")

    for zid, status, base in report:
        print("%-14s %-28s %s" % (zid, status, base))
    print("\n%d zones written, %.0f KB" % (len(out), os.path.getsize(OUT)/1024))

if __name__ == '__main__':
    main()


def inject():
    """Drop the generated data into index.html between the ZONEMAPS markers."""
    page = r"C:\Users\sigha\OneDrive\Documents\EQLTravel\index.html"
    data = open(OUT, encoding="utf-8").read().strip()
    html = open(page, encoding="utf-8").read()
    a, b = "<!-- ZONEMAPS -->", "<!-- /ZONEMAPS -->"
    i, j = html.index(a), html.index(b)
    html = html[:i] + a + "\n<script>" + data + "</script>\n" + html[j:]
    open(page, "w", encoding="utf-8").write(html)
    print("injected into index.html (%.0f KB total)" % (len(html)/1024))

if __name__ == '__main__':
    inject()
