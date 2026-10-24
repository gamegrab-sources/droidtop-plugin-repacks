"""Tests for the Repacks plugin (python3 test_plugin.py, after build.sh: it also loads the built
plugin.py with gamegrab embedded). The pages below are small hand-written samples in the
markup the sites use, not copies of their pages."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, "common"), os.path.join(HERE, "src")]

import gamegrab as gg  # noqa: E402
import plugin  # noqa: E402
from testing import FakeHost, envelope, install  # noqa: E402

FG_SEARCH = """<main>
<article id="post-1" class="post-1 post type-post status-publish category-lossless-repack">
<h1 class="entry-title"><a href="https://fitgirl-repacks.site/sample-game/" rel="bookmark">Sample Game &#8211; v1.0.2 + 2 DLCs</a></h1>
<div class="entry-summary"><p>#1 Sample Game Company: Studio Original Size: 2.2 GB Repack Size: 1.6 GB Download Mirrors</p></div></article>
<article id="post-2" class="post-2 post type-post status-publish category-updates-digest">
<h1 class="entry-title"><a href="https://fitgirl-repacks.site/updates-digest/">Updates Digest for May 1</a></h1></article>
</main>"""

FG_POST = """<html><head><title>Sample Game &#8211; v1.0.2 + 2 DLCs - FitGirl Repacks</title></head><body>
<h1 class="entry-title">Sample Game &#8211; v1.0.2 + 2 DLCs</h1>
<div class="entry-content">
<p>Genres/Tags: <a href="/tag/a/">Arcade</a><br />Company: <strong>Studio</strong><br />Languages: <strong>ENG</strong><br />Original Size: <strong>2.2 GB</strong><br />Repack Size: <strong>1.6 GB</strong></p>
<h3>Download Mirrors (Direct Links)</h3>
<ul>
<li><a href="https://paste.fitgirl-repacks.site/?x#y">Filehoster: FastHost</a> (fast)
<div class="su-spoiler"><div class="su-spoiler-content">
<a href="https://fasthost.example/a1#Sample_Game.part1.rar">Sample_Game.part1.rar</a><br />
<a href="https://fasthost.example/a2#Sample_Game.part2.rar">Sample_Game.part2.rar</a>
</div></div></li>
<li><a href="https://paste.fitgirl-repacks.site/?z">Filehoster: MultiUpload</a> (10+ hosters)</li>
</ul>
<h3>Download Mirrors (Torrent)</h3>
<ul>
<li><a href="https://tracker.example/torrent/1/">1337x</a> | [<a href="magnet:?xt=urn:btih:AAE9343B427EF01A2C6DDDAE3F4CD04E0FC838DC&#038;dn=Sample">magnet</a>] [<a href="https://paste.fitgirl-repacks.site/?q">.torrent file only</a>]</li>
</ul>
</div><!-- .entry-content -->
</body></html>"""

DODI_POST = """<html><head><title>12- Sample Game (v1.5 + All DLCs + MULTi10) [DODI Repack] &#8211; DODI Repacks</title></head><body>
<h1 class="entry-title">12- Sample Game (v1.5 + All DLCs + MULTi10) [DODI Repack]</h1>
<div class="entry-content"><p><strong>Repack Size</strong> : From 860 MB<br />Final Size : 8 GB</p>
<p><strong>Download Links</strong></p>
<p><strong>Torrent &#8211; <a href="https://torrenthost.example/f1">Click Here</a> &#8211; or &#8211; <a href="https://torrenthost2.example/f2">Click Here</a></strong></p>
<p><strong>DataHost &#8211; <a href="http://shortlink.example/abc">Click Here</a></strong></p>
</div><!-- .entry-content --></body></html>"""

EA_HOME = """<html><body>
<h1>09.10.2026</h1>
<h3>Sample Game Deluxe Edition ElAmigos +[Update 1.4.2] <a href="data/Sample_Game_Deluxe_Edition_MULTi15_-_ElAmigos.html">DOWNLOAD</a></h3>
<h5>Another Title ElAmigos <a href="data/Another_Title_-_ElAmigos.html">DOWNLOAD</a></h5>
<h1>01.10.2026</h1>
<h3>Old Game ElAmigos <a href="data/Old_Game_-_ElAmigos.html">DOWNLOAD</a></h3>
</body></html>"""

EA_GAME = """<html><body><h2>Sample Game Deluxe Edition (2026), 1.28GB</h2>
<h3>ElAmigos release. Updated till 08.10.2026.</h3>
<h2>DDOWNLOAD</h2><h3><a href="https://linkcheck.example/Container/1.html">https://linkcheck.example/Container/1.html</a></h3>
<h2>RAPIDGATOR</h2><h3><a href="https://linkcheck.example/Container/2.html">https://linkcheck.example/Container/2.html</a></h3>
</body></html>"""

FG_HOME = """<main>
<article id="post-9" class="post-9 post type-post status-publish category-uncategorized">
<h1 class="entry-title"><a href="https://fitgirl-repacks.site/upcoming-repacks-10/">Upcoming Repacks</a></h1></article>
<article id="post-8" class="post-8 post type-post status-publish category-updates-digest">
<h1 class="entry-title"><a href="https://fitgirl-repacks.site/updates-digest-for-may-2/">Updates Digest for May 2</a></h1></article>
<article id="post-7" class="post-7 post type-post status-publish category-lossless-repack">
<h1 class="entry-title"><a href="https://fitgirl-repacks.site/new-game/">New Game &#8211; v2.0</a></h1>
<div class="entry-content"><p>Repack Size: <strong>3 GB</strong></p></div></article>
<article id="post-6" class="post-6 post type-post status-publish category-lossless-repack">
<h1 class="entry-title"><a href="https://fitgirl-repacks.site/older-game/">Older Game &#8211; v1.1</a></h1></article>
</main>"""

DODI_HOME = """<main>
<article id="post-5" class="post-5 post type-post status-publish sticky category-uncategorized">
<header class="entry-header"><h3 class="entry-title"><a href="https://dodi-repacks.site/upcoming-repacks/">Upcoming Repacks</a></h3></header></article>
<article id="post-4" class="post-4 post type-post status-publish category-uncategorized">
<header class="entry-header"><h3 class="entry-title"><a href="https://dodi-repacks.site/dodi-game/">2244- Dodi Game (v1.11 + All DLCs + MULTi14) (From 43.4 GB) [DODI Repack]</a></h3></header>
<div class="entry-content"><p><strong>Repack Size</strong> : From 43.4 GB</p></div></article>
<article id="post-3" class="post-3 post type-post status-publish category-uncategorized">
<header class="entry-header"><h3 class="entry-title"><a href="https://dodi-repacks.site/new-repack-team/">New Repack Team</a></h3></header></article>
</main>"""

PAGES = {
    "https://fitgirl-repacks.site/?s=sample+game": FG_SEARCH,
    "https://fitgirl-repacks.site/sample-game/": FG_POST,
    "https://dodi-repacks.site/?s=sample+game": "<main></main>",
    "https://dodi-repacks.site/sample-game/": DODI_POST,
    "https://elamigos.site/": EA_HOME,
    "https://fitgirl-repacks.site/": FG_HOME,
    "https://dodi-repacks.site/": DODI_HOME,
    "https://elamigos.site/data/Sample_Game_Deluxe_Edition_MULTi15_-_ElAmigos.html": EA_GAME,
}


def call(point, op, args=None):
    return json.loads(plugin.handle(envelope(point, op, args)))


def job(point, op, args=None):
    return json.loads(plugin.start_job("j", json.loads(envelope(point, op, args)), lambda p, s: None))


def buttons(page):
    return [n for s in page["sections"] for n in s["items"] if n["type"] == "button"]


class Titles(unittest.TestCase):
    def test_titles(self):
        self.assertEqual(plugin.split_fitgirl("Hollow Knight: Silksong – v1.0.28324"), ("Hollow Knight: Silksong", "v1.0.28324"))
        self.assertEqual(plugin.split_fitgirl("Game – Build 123 + 3 DLCs"), ("Game", "Build 123"))
        self.assertEqual(plugin.split_fitgirl("Maseylia: Echoes of the Past"), ("Maseylia: Echoes of the Past", None))
        self.assertEqual(plugin.split_dodi("2183- Hollow Knight: Silksong (v1.0.29242 + Soundtrack Collection + MULTi10) [DODI Repack]"), ("Hollow Knight: Silksong", "v1.0.29242"))
        self.assertEqual(
            plugin.split_dodi("1138- Hot Wheels Unleashed: Game of the Year Edition (Build 9946223 – Update 29 + All DLCs + MULTi14) – [DODI Repack]"),
            ("Hot Wheels Unleashed: Game of the Year Edition", "Build 9946223 – Update 29"),
        )
        self.assertEqual(plugin.split_elamigos("Control Resonant Deluxe Edition ElAmigos +[Update 1.4.2]"), ("Control Resonant Deluxe Edition", "Update 1.4.2"))
        self.assertEqual(plugin.split_elamigos("Neon Abyss 2 Deluxe Edition ElAmigos"), ("Neon Abyss 2 Deluxe Edition", None))


class Repacks(unittest.TestCase):
    def setUp(self):
        self.host = install(gg, FakeHost(PAGES))

    def test_search_every_site(self):
        rows = call("library.sources", "search", {"query": "sample game"})["data"]["results"]
        self.assertEqual([(r["badges"][0], r["title"]) for r in rows], [("FitGirl", "Sample Game"), ("ElAmigos", "Sample Game Deluxe Edition")])
        self.assertEqual(rows[0]["columns"], ["v1.0.2", "1.6 GB"])
        self.assertEqual(rows[1]["columns"], ["Update 1.4.2", "09.10.2026"])

    def test_featured_takes_each_site_newest_first_in_turn(self):
        rows = call("library.sources", "featured", {"limit": 10})["data"]["results"]
        self.assertEqual(
            [(r["badges"][0], r["title"]) for r in rows],
            [
                ("FitGirl", "New Game"),
                ("DODI", "Dodi Game"),
                ("ElAmigos", "Sample Game Deluxe Edition"),
                ("FitGirl", "Older Game"),
                ("ElAmigos", "Another Title"),
                ("ElAmigos", "Old Game"),
            ],
        )
        self.assertEqual(rows[0]["columns"], ["v2.0", "3 GB"])
        self.assertEqual(rows[1]["columns"], ["v1.11", "From 43.4 GB"])
        self.assertEqual(len(call("library.sources", "featured", {"limit": 2})["data"]["results"]), 2)
        self.assertEqual(call("library.sources", "featured", {"platform": "snes", "limit": 2})["data"]["results"], [])
        call("ui.facets", "setSite", {"site": "fitgirl", "value": False})
        call("ui.facets", "setSite", {"site": "dodi", "value": False})
        self.assertEqual([r["badges"][0] for r in call("library.sources", "featured", {"limit": 2})["data"]["results"]], ["ElAmigos", "ElAmigos"])
        call("ui.facets", "setSite", {"site": "elamigos", "value": False})
        self.assertEqual(call("library.sources", "featured", {"limit": 2})["data"]["results"], [])

    def test_featured_leaves_out_a_site_it_cannot_read(self):
        del self.host.pages["https://dodi-repacks.site/"]
        rows = call("library.sources", "featured", {"limit": 3})["data"]["results"]
        self.assertEqual([r["badges"][0] for r in rows], ["FitGirl", "ElAmigos", "FitGirl"])

    def test_site_toggles(self):
        call("ui.facets", "setSite", {"site": "fitgirl", "value": False})
        call("ui.facets", "setSite", {"site": "elamigos", "value": False})
        toggles = call("ui.facets", "get", {"target": "settings.page"})["data"]["facets"]
        self.assertEqual([(f["id"], f["value"]) for f in toggles], [("fitgirl", False), ("dodi", True), ("elamigos", False)])
        self.assertEqual(call("ui.facets", "get", {"target": "quickmenu"})["data"]["facets"], [])
        self.assertEqual(call("ui.facets", "setSite", {"site": "nope", "value": True})["error"]["code"], "INVALID_ARGS")
        call("library.sources", "search", {"query": "sample game"})
        self.assertEqual(self.host.requests(), ["https://dodi-repacks.site/?s=sample+game"])

    def test_fitgirl_release(self):
        page = call("library.sources", "detail", {"ref": {"site": "fitgirl", "url": "https://fitgirl-repacks.site/sample-game/"}})["data"]
        titles = [s.get("title") for s in page["sections"]]
        self.assertEqual(titles, [None, "Torrent", "FastHost"])
        b = buttons(page)
        magnet = [x for x in b if x["id"].startswith("magnet")][0]
        self.assertTrue(magnet["action"]["args"]["uri"].startswith("magnet:?xt=urn:btih:AAE9343B427EF01A2C6DDDAE3F4CD04E0FC838DC&dn=Sample"))
        self.assertEqual(magnet["title"], "1337x")
        parts = [x for x in b if x["id"].startswith("web")]
        self.assertEqual([p["title"] for p in parts], ["Sample_Game.part1.rar", "Sample_Game.part2.rar"])
        whole = [x for x in b if x["id"].startswith("parts-")][0]
        self.assertEqual(whole["title"], "Download all 2 parts")
        self.assertEqual(whole["action"]["op"], "acquireParts")

    def test_all_parts_as_one_acquire(self):
        ref = {"site": "fitgirl", "url": "https://fitgirl-repacks.site/sample-game/"}
        opened = []

        def capture(link):
            opened.append(link)
            name = link.split("#", 1)[1]
            return {"url": "https://cdn.example/" + name, "fileName": name, "session": "w-00000000-0000-0000-0000-00000000000%d" % len(opened)}

        self.host.captured = capture
        result = job("library.sources", "acquireParts", {"ref": ref, "group": "FastHost"})
        self.assertTrue(result["ok"], result)
        downloads = json.loads(result["values"]["downloads"])
        self.assertEqual([d["fileName"] for d in downloads], ["Sample_Game.part1.rar", "Sample_Game.part2.rar"])
        self.assertEqual({d["unpack"] for d in downloads}, {"archive"})
        self.assertEqual(len(opened), 2)
        self.host.captured = lambda link: None
        self.assertIn("Part 1 of 2", job("library.sources", "acquireParts", {"ref": ref, "group": "FastHost"})["error"])

    def test_handoff(self):
        uri = "magnet:?xt=urn:btih:AAE9343B427EF01A2C6DDDAE3F4CD04E0FC838DC"
        self.assertEqual(job("library.sources", "handoff", {"uri": uri, "title": "x"})["values"]["message"], "Opened in your torrent app")
        self.assertEqual(job("library.sources", "handoff", {"uri": "https://torrenthost.example/f1"})["values"]["message"], "Opened in your browser")
        self.host.handoff = False
        self.assertIn("view", job("library.sources", "handoff", {"uri": uri})["values"])

    def test_direct_link_download_through_the_web_view(self):
        ref = {"site": "fitgirl", "url": "https://fitgirl-repacks.site/sample-game/"}
        self.host.captured = {"url": "https://cdn.example/Sample_Game.part1.rar", "fileName": "Sample_Game.part1.rar", "session": "w-00000000-0000-0000-0000-000000000000"}
        result = job("library.sources", "acquire", {"ref": ref, "link": "https://fasthost.example/a1#Sample_Game.part1.rar"})
        self.assertTrue(result["ok"], result)
        self.assertEqual(json.loads(result["values"]["download"])["fileName"], "Sample_Game.part1.rar")
        refused = job("library.sources", "acquire", {"ref": ref, "link": "https://elsewhere.example/x"})
        self.assertFalse(refused["ok"])

    def test_dodi_release(self):
        page = call("library.sources", "detail", {"ref": {"site": "dodi", "url": "https://dodi-repacks.site/sample-game/"}})["data"]
        b = buttons(page)
        self.assertEqual([x["title"] for x in b if x["id"].startswith("page-")], ["Torrent link 1", "Torrent link 2"])
        self.assertEqual([x["title"] for x in b if x["id"].startswith("web-")], ["DataHost link 1"])
        self.assertIn(("Version", "v1.5"), [(n["title"], n.get("value")) for n in page["sections"][0]["items"]])

    def test_elamigos_release(self):
        url = "https://elamigos.site/data/Sample_Game_Deluxe_Edition_MULTi15_-_ElAmigos.html"
        page = call("library.sources", "detail", {"ref": {"site": "elamigos", "url": url}})["data"]
        self.assertEqual(page["title"], "Sample Game Deluxe Edition")
        self.assertEqual([s.get("title") for s in page["sections"]], [None, "Ddownload", "Rapidgator"])

    def test_updates(self):
        found = call("library.updates", "resolve", {"source": "fitgirl", "text": "https://fitgirl-repacks.site/sample-game/"})["data"]["found"]
        self.assertEqual(found["id"], "sample-game")
        self.assertEqual(call("library.updates", "resolve", {"source": "dodi", "text": "https://fitgirl-repacks.site/sample-game/"})["data"], {})
        answers = call("library.updates", "check", {"source": "fitgirl", "ids": ["sample-game", "gone-game"]})["data"]["answers"]
        self.assertEqual(answers, [{"id": "sample-game", "url": "https://fitgirl-repacks.site/sample-game/", "version": "v1.0.2"}, {"id": "gone-game", "gone": True}])
        ea = call("library.updates", "check", {"source": "elamigos", "ids": ["Sample_Game_Deluxe_Edition_MULTi15_-_ElAmigos.html", "Missing.html"]})["data"]["answers"]
        self.assertEqual(ea[0]["version"], "Update 1.4.2")
        self.assertTrue(ea[1]["gone"])
        dodi = call("library.updates", "check", {"source": "dodi", "ids": ["sample-game"]})["data"]["answers"]
        self.assertEqual(dodi[0]["version"], "v1.5")

    def test_new_version_is_notified_once(self):
        call("library.updates", "check", {"source": "fitgirl", "ids": ["sample-game"]})
        self.host.pages["https://fitgirl-repacks.site/sample-game/"] = FG_POST.replace("v1.0.2", "v1.0.3")
        call("library.updates", "check", {"source": "fitgirl", "ids": ["sample-game"]})
        call("library.updates", "check", {"source": "fitgirl", "ids": ["sample-game"]})
        self.assertEqual(len(self.host.notes), 1)
        self.assertIn("v1.0.3", self.host.notes[0]["text"])

    def test_match(self):
        c = call("library.updates", "match", {"source": "elamigos", "title": "Sample Game Deluxe Edition"})["data"]["candidates"]
        self.assertEqual(c[0]["id"], "Sample_Game_Deluxe_Edition_MULTi15_-_ElAmigos.html")


class Built(unittest.TestCase):
    def test_built_plugin_loads(self):
        built = os.path.join(HERE, "build", "plugin.py")
        if not os.path.exists(built):
            self.skipTest("run build.sh first")
        with open(built, encoding="utf-8") as f:
            source = f.read()
        scope = {"__name__": "built"}
        exec(compile(source, "plugin.py", "exec"), scope)
        install(scope["gg"], FakeHost())
        self.assertTrue(json.loads(scope["handle"](envelope("ui.facets", "get", {"target": "settings.page"})))["ok"])


if __name__ == "__main__":
    unittest.main()
