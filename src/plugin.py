"""Repacks for droidtop: FitGirl, DODI and ElAmigos in one unofficial gamegrab-sources plugin,
not part of droidtop and not affiliated with any of them.

A python-kind plugin (droidtop docs/plugin-api.md 3):
- `library.sources` (A2), Get games: searches the sites the person turned on, from their
  public search pages (FitGirl, DODI) and release list (ElAmigos); a release's page lists
  its download options: torrents (magnet links) go to a torrent app the person installed,
  because droidtop has no torrent client; direct links open in droidtop's web view with
  the plugin's session, where the person goes through the file host's own page, and the
  download it starts runs in droidtop's Downloads into the game folder.
- `library.updates` (A6), one source per site: a game linked to a release page is checked
  for a newer version from that page's title.
- `ui.settings`: a toggle per site.

It runs contained (5.3): requests go through droidtop's `net.http` and `net.download`
(pages over 128 KiB), state through droidtop's data API, and it draws nothing itself.
"""
import json
import re
import time
from urllib.parse import quote_plus, urlparse

import gamegrab as gg  # embedded by build.sh

SITES = {
    "fitgirl": {"label": "FitGirl", "host": "fitgirl-repacks.site"},
    "dodi": {"label": "DODI", "host": "dodi-repacks.site"},
    "elamigos": {"label": "ElAmigos", "host": "elamigos.site"},
}

SETTINGS = "settings.json"
STATE = "state.json"
SEARCH_CACHE_S = 30 * 60
DETAIL_CACHE_S = 12 * 3600
ELAMIGOS_LIST_CACHE_S = 6 * 3600
CHECK_BUDGET_S = 90
MAX_RESULTS_PER_SITE = 30

plugin = gg.Plugin("Repacks")


def settings():
    kept = gg.read_json(SETTINGS, {}) or {}
    return {site: bool(kept.get(site, True)) for site in SITES}


def site_of_url(url):
    host = (urlparse(url or "").hostname or "").lower()
    for key, s in SITES.items():
        if host == s["host"] or host.endswith("." + s["host"]):
            return key
    return None


# ------------------------------------------------------------------ titles and versions


def split_fitgirl(title):
    """`Name – v1.0.2 + 3 DLCs` -> (name, version)."""
    title = gg.unescape(title).strip()
    parts = re.split(r"\s+[–—-]\s+(?=(?:v\s*\d|build|update|r\d|\d))", title, maxsplit=1, flags=re.I)
    if len(parts) == 2:
        version = re.split(r"\s+\+\s+", parts[1])[0].strip().rstrip(",")
        return parts[0].strip(), version or None
    return title, None


def split_dodi(title):
    """`2183- Name (v1.0.2 + Soundtrack + MULTi10) [DODI Repack]` -> (name, version)."""
    title = gg.unescape(title).strip()
    title = re.sub(r"^\d+\s*-\s*", "", title)
    title = re.sub(r"\s*[–-]?\s*\[DODI Repack\]\s*$", "", title, flags=re.I).strip()
    m = re.search(r"\(([^()]*)\)\s*(?:\(.*\))?\s*$", title)
    version = None
    name = title
    if m:
        first = re.split(r"\s+\+\s+", m.group(1))[0].strip()
        if re.match(r"(?i)^(v\s*\d|build|update|r\d|\d)", first):
            version = first
        name = title[: m.start()].strip()
        name = re.sub(r"\s*\([^()]*\)\s*$", "", name).strip() or name
    return name, version


def split_elamigos(line):
    """`Name ElAmigos +[Update 1.4.2]` -> (name, version)."""
    line = gg.unescape(line).strip()
    m = re.search(r"\[(Update[^\]]*|v\s*\d[^\]]*|Build[^\]]*)\]", line, flags=re.I)
    version = m.group(1).strip() if m else None
    name = re.split(r"\s+ElAmigos\b", line, maxsplit=1, flags=re.I)[0].strip()
    return name, version


def fact(text, label):
    """The value after `label:` on its line."""
    m = re.search(r"%s\s*:\s*([^\n]+?)\s*(?:\n|$)" % label, text or "", flags=re.I)
    return gg.human_size(m.group(1)).rstrip(".") if m else None


_SIZE = r"(?:from\s+)?[\d.,]+\s*[KMGT]i?B(?:\s*/\s*[\d.,]+\s*[KMGT]i?B)?"


def size_from(text, label):
    """A size after `label:` (`1.6 GB`, `From 860 MB`, `814 MB/1 GB`), wherever the line ends."""
    m = re.search(r"%s\s*:\s*(%s)" % (label, _SIZE), text or "", flags=re.I)
    return gg.human_size(m.group(1)) if m else None


# ------------------------------------------------------------------ search


def articles(page):
    return re.findall(r"(?is)<article\b([^>]*)>(.*?)</article>", page or "")


def search_wordpress(site, query):
    s = SITES[site]
    url = "https://%s/?s=%s" % (s["host"], quote_plus(query))

    def produce():
        answer = gg.http(url)
        if not answer.ok:
            raise gg.HostError("FAILED", gg.http_error(s["label"], answer.status))
        out = []
        for attrs, body in articles(answer.body):
            if "type-post" not in attrs or "category-updates-digest" in attrs:
                continue
            m = re.search(r'(?is)<h[12] class="entry-title"[^>]*>\s*<a href="([^"]+)"[^>]*>(.*?)</a>', body)
            if not m:
                continue
            title = gg.one_line(m.group(2))
            name, version = (split_fitgirl if site == "fitgirl" else split_dodi)(title)
            summary = gg.strip_tags(body)
            out.append(
                {
                    "site": site,
                    "id": slug_of(m.group(1)),
                    "url": m.group(1),
                    "title": title,
                    "name": name,
                    "version": version,
                    "size": size_from(summary, "Repack Size"),
                }
            )
        return out

    return gg.cached("search-" + url, SEARCH_CACHE_S, produce)


def slug_of(url):
    path = urlparse(url).path.strip("/")
    return path.split("/")[-1] if path else ""


def elamigos_list():
    """ElAmigos' whole release list, from its home page (about 500 KB, so it comes through
    net.download): [{id, url, line, name, version, date}]."""

    def produce():
        page = gg.download_text("https://elamigos.site/", "scratch-elamigos.html")
        try:
            gg.delete("scratch-elamigos.html")
        except gg.HostError:
            pass
        return parse_elamigos_list(page)

    return gg.cached("elamigos-list", ELAMIGOS_LIST_CACHE_S, produce)


def parse_elamigos_list(page):
    out = []
    seen = set()
    date = None
    for m in re.finditer(r'(?is)<h1>([^<]*)</h1>|<h[35]>((?:(?!</?h\d).)*?)<a href="(data/[^"]+\.html)"[^>]*>\s*DOWNLOAD\s*</a>\s*</h[35]>', page or ""):
        if m.group(1) is not None:
            if re.fullmatch(r"\s*\d{2}\.\d{2}\.\d{4}\s*", m.group(1)):
                date = m.group(1).strip()
            continue
        line = gg.one_line(m.group(2))
        name, version = split_elamigos(line)
        file = m.group(3).split("/", 1)[1]
        if file in seen:
            continue  # listed again under an older date: the newest line (first) is current
        seen.add(file)
        out.append({"site": "elamigos", "id": file, "url": "https://elamigos.site/" + m.group(3), "title": line, "name": name, "version": version, "date": date})
    return out


def search_elamigos(query):
    return [dict(r, size=None) for r in elamigos_list() if gg.matches_all(r["title"], query)]


def search(query, sites):
    results = []
    failures = []
    for site in sites:
        try:
            found = search_elamigos(query) if site == "elamigos" else search_wordpress(site, query)
        except gg.HostError as e:
            failures.append(e)
            continue
        results.extend(found[:MAX_RESULTS_PER_SITE])
    if failures and len(failures) == len(sites):
        raise failures[0]
    return results


def result_row(r):
    return {
        "id": "%s-%s" % (r["site"], r["id"]),
        "title": r["name"] or r["title"],
        "subtitle": r["title"] if r["title"] != r["name"] else None,
        "columns": [c for c in (r.get("version"), r.get("size"), r.get("date")) if c],
        "badges": [SITES[r["site"]]["label"]],
        "ref": {"site": r["site"], "url": r["url"]},
    }


# ------------------------------------------------------------------ a release's page


def release(site, url):
    """What a release page offers: {title, name, version, facts: [(label, value)], options}.
    An option is {kind: magnet|web|page, group, label, link}: magnet links go to a torrent
    app, web links open in droidtop's web view (the download they start is captured), page
    links are pages a person opens in a browser (a .torrent file on a file host)."""

    def produce():
        answer = gg.get_page(url, "scratch-release.html")
        if answer.status == 404:
            return None
        if not answer.ok:
            raise gg.HostError("FAILED", gg.http_error(SITES[site]["label"], answer.status))
        return parse_release(site, answer.body, url)

    return gg.cached("release-" + url, DETAIL_CACHE_S, produce)


def _content(page):
    m = re.search(r'(?is)<div class="entry-content"[^>]*>(.*?)<!-- \.entry-content -->', page or "")
    if m:
        return m.group(1)
    m = re.search(r'(?is)<div class="entry-content"[^>]*>(.*)', page or "")
    return m.group(1) if m else ""


def _title(page):
    m = re.search(r'(?is)<h1 class="entry-title"[^>]*>(.*?)</h1>', page or "")
    if m:
        return gg.one_line(m.group(1))
    m = re.search(r"(?is)<title>(.*?)</title>", page or "")
    return re.split(r"\s+[–-]\s+(?:FitGirl Repacks|DODI Repacks)\s*$", gg.one_line(m.group(1)))[0] if m else ""


def parse_release(site, page, url):
    if site == "fitgirl":
        return parse_fitgirl(page)
    if site == "dodi":
        return parse_dodi(page)
    return parse_elamigos(page, url)


def parse_fitgirl(page):
    title = _title(page)
    name, version = split_fitgirl(title)
    body = _content(page)
    text = gg.strip_tags(body)
    facts = []
    for label in ("Genres/Tags", "Company", "Companies", "Languages", "Original Size", "Repack Size"):
        value = fact(text, re.escape(label))
        if value:
            facts.append((label, value))
    options = []
    # Torrents: every magnet link, named after the tracker the line names first.
    for li in re.findall(r"(?is)<li\b[^>]*>(.*?)</li>", body):
        found = [(h, t) for h, t in gg.links(li) if h.startswith("magnet:")]
        if found:
            named = [t for h, t in gg.links(li) if h.startswith("http") and t and t.lower() not in ("magnet", ".torrent file only")]
            group = named[0] if named else "Torrent"
            options.append({"kind": "magnet", "group": "Torrent", "label": group, "link": found[0][0]})
    # Direct links: each file host's parts, from its "Click to show direct links" list.
    for li in re.findall(r"(?is)<li\b[^>]*>(.*?)</li>", body):
        host = re.search(r"(?is)Filehoster:\s*([^<]+)</a>", li)
        if not host:
            continue
        spoiler = re.search(r'(?is)<div class="su-spoiler-content[^"]*"[^>]*>(.*)', li)
        parts = [(h, t) for h, t in gg.links(spoiler.group(1) if spoiler else "") if h.startswith("https://") and site_of_url(h) is None]
        for h, t in parts:
            options.append({"kind": "web", "group": host.group(1).strip(), "label": t or h, "link": h})
    return {"title": title, "name": name, "version": version, "facts": facts, "options": options}


def parse_dodi(page):
    title = _title(page)
    name, version = split_dodi(title)
    body = _content(page)
    text = gg.strip_tags(body)
    facts = []
    for label in ("Game Version", "Languages?", "Repack Size", "Final Size", "GENRE", "DEVELOPER"):
        value = fact(text, label)
        if value:
            facts.append((label.rstrip("?").title() if label.isupper() else label.rstrip("?"), value))
    options = []
    links_part = body.split("Download Links", 1)[-1] if "Download Links" in body else body
    for h, t in gg.links(links_part):
        if h.startswith("magnet:"):
            options.append({"kind": "magnet", "group": "Torrent", "label": "Magnet link", "link": h})
    for p in re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", links_part):
        found = [(h, t) for h, t in gg.links(p) if h.startswith(("https://", "http://")) and site_of_url(h) is None]
        if not found:
            continue
        group = re.split(r"\s+[–-]\s+", gg.one_line(p), maxsplit=1)[0].strip() or "Download"
        torrent = group.lower().startswith("torrent")
        for i, (h, t) in enumerate(found, 1):
            options.append(
                {
                    "kind": "page" if torrent else "web",
                    "group": group,
                    "label": "%s link %d" % (group, i),
                    "link": h,
                }
            )
    return {"title": title, "name": name, "version": version, "facts": facts, "options": options}


def parse_elamigos(page, url):
    m = re.search(r"(?is)<h2>(.*?)</h2>", page or "")
    title = gg.one_line(m.group(1)) if m else slug_of(url)
    name = re.sub(r"\s*\(\d{4}\)\s*,?.*$", "", title).strip() or title
    size = re.search(r",\s*([\d.,]+\s*[KMGT]B)\s*$", title)
    facts = []
    if size:
        facts.append(("Size", size.group(1)))
    updated = re.search(r"Updated till ([\d.]+)", page or "")
    if updated:
        facts.append(("Updated", updated.group(1).rstrip(".")))
    version = None
    options = []
    group = None
    for m in re.finditer(r"(?is)<h2>(.*?)</h2>|<h3>(.*?)</h3>", page or ""):
        if m.group(1) is not None:
            group = gg.one_line(m.group(1))
            continue
        for h, t in gg.links(m.group(2)):
            if group and h.startswith("https://") and site_of_url(h) is None:
                host = urlparse(h).hostname or h
                options.append({"kind": "web", "group": group.title(), "label": "%s via %s" % (group.title(), host), "link": h})
    return {"title": title, "name": name, "version": version, "facts": facts, "options": options}


WEB_NOTE = "Opens the file host's page. The download it starts goes to Downloads."
PARTS_NOTE = "Opens each part's page in turn and downloads the parts as one."
SESSION_DENIED = 'Turn on "Use your signed-in session" in this plugin\'s Permissions to open direct links.'
PARTS_TOO_MANY = "%d parts is more than one download takes. Download them one by one into the same folder."


def part_members(members):
    """The web options of one file host that are the numbered parts of one archive, in order; else []."""
    web = [o for o in members if o["kind"] == "web"]
    if len(web) < 2 or not gg.is_split_set([o["label"] for o in web]):
        return []
    return sorted(web, key=lambda o: gg.split_part(o["label"])[1])
PAGE_NOTE = "Opens in your browser. Its .torrent file goes to your torrent app."


def detail_view(site, url, r):
    items = [gg.info("site", "From", SITES[site]["label"])]
    if r.get("version"):
        items.append(gg.info("version", "Version", r["version"]))
    for label, value in r.get("facts") or []:
        items.append(gg.info("fact-" + gg.name_key(label), label, gg.cut(value, 200)))
    items.append(gg.button("page", "Open the release page", gg.job("handoff", "Open the release page", {"uri": url, "title": r.get("name") or ""}), subtitle="In your browser"))
    sections = [gg.section("main", items)]
    options = r.get("options") or []
    torrents = [o for o in options if o["kind"] == "magnet"]
    if torrents:
        rows = []
        for i, o in enumerate(torrents):
            rows.append(gg.button("magnet-%d" % i, o["label"], gg.job("handoff", "Open in a torrent app", {"uri": o["link"], "title": r.get("name") or ""}), subtitle=gg.TORRENT_NOTE))
        sections.append(gg.section("torrents", rows, "Torrent"))
    web = [o for o in options if o["kind"] in ("web", "page")]
    groups = []
    for o in web:
        if o["group"] not in groups:
            groups.append(o["group"])
    for g in groups[:8]:
        rows = []
        members = [o for o in web if o["group"] == g]
        parts = part_members(members)
        if parts and len(parts) <= gg.MAX_DOWNLOADS:
            rows.append(
                gg.button(
                    "parts-" + gg.name_key(g),
                    "Download all %d parts" % len(parts),
                    gg.job("acquireParts", "Download %s" % (r.get("name") or ""), {"ref": {"site": site, "url": url}, "group": g}),
                    subtitle=PARTS_NOTE,
                )
            )
        elif parts:
            rows.append(gg.info("parts-" + gg.name_key(g), "Several parts", subtitle=PARTS_TOO_MANY % len(parts)))
        for i, o in enumerate(members[:40]):
            if o["kind"] == "web":
                action = gg.job("acquire", "Download %s" % (r.get("name") or ""), {"ref": {"site": site, "url": url}, "link": o["link"], "label": o["label"]})
                rows.append(gg.button("web-%s-%d" % (gg.name_key(g), i), gg.cut(o["label"], 200), action, subtitle=WEB_NOTE if i == 0 else None))
            else:
                action = gg.job("handoff", "Open in your browser", {"uri": o["link"], "title": r.get("name") or ""})
                rows.append(gg.button("page-%s-%d" % (gg.name_key(g), i), gg.cut(o["label"], 200), action, subtitle=PAGE_NOTE if i == 0 else None))
        sections.append(gg.section("g-" + gg.name_key(g)[:40], rows, g))
    if not options:
        sections.append(gg.section("none", [gg.info("none", "No download links found", subtitle="Open the release page to see what it offers.")]))
    return gg.view(gg.cut(r.get("name") or r.get("title") or "Release", 200), [], sections=sections[:12])


# ------------------------------------------------------------------ library.sources (A2)


@plugin.on("library.sources", "form")
def _form(args):
    s = settings()
    options = [("all", "All sites")] + [(k, v["label"]) for k, v in SITES.items() if s[k]]
    return gg.ok(gg.view("Search repacks", [gg.text("query", "Search", ""), gg.choice("site", "Where", options, value="all")]))


@plugin.on("library.sources", "search")
def _search(args):
    values = args.get("values") or {}
    query = (args.get("query") or values.get("query") or "").strip()[:100]
    if not gg.words(query):
        return gg.ok({"results": []})
    s = settings()
    which = values.get("site") or "all"
    sites = [k for k in SITES if s[k] and (which == "all" or k == which)]
    return gg.ok({"results": [result_row(r) for r in search(query, sites)]})


@plugin.on("library.sources", "detail")
def _detail(args):
    ref = args.get("ref") or {}
    url = str(ref.get("url") or "")
    site = site_of_url(url)
    if site is None or ref.get("site") != site:
        return gg.error("INVALID_ARGS", "Missing release")
    r = release(site, url)
    if r is None:
        return gg.error("NOT_FOUND", "That release page is gone")
    return gg.ok(detail_view(site, url, r))


@plugin.job("library.sources", "acquire")
def _acquire(args, report):
    ref = args.get("ref") or {}
    url = str(ref.get("url") or "")
    site = site_of_url(url)
    link = str(args.get("link") or "")
    if site is None or not link.startswith("https://"):
        return gg.failed("Choose a download link first")
    r = release(site, url) or {}
    if link not in [o["link"] for o in r.get("options") or [] if o["kind"] == "web"]:
        return gg.failed("That link is no longer on the release page; open it again")
    report(-1, "Opening %s" % (urlparse(link).hostname or "the file host"))
    try:
        download = gg.open_in_session(link)
    except gg.HostError as e:
        if e.code == "PERMISSION_DENIED":
            return gg.failed(SESSION_DENIED)
        raise
    if download is None:
        return gg.failed("No download was started on that page")
    return gg.done("Downloading %s" % (r.get("name") or "the release"), download=download)


@plugin.job("library.sources", "handoff")
def _handoff(args, report):
    uri = str(args.get("uri") or "")
    title = str(args.get("title") or "Link")
    if not (uri.startswith("magnet:?xt=urn:btih:") or uri.startswith("https://") or uri.startswith("http://")):
        return gg.failed("Missing link")
    if uri.startswith("magnet:"):
        return gg.handoff_result(uri, title, "Opened in your torrent app", gg.TORRENT_NOTE + " Install one to open magnet links.")
    return gg.handoff_result(uri, title, "Opened in your browser", "Open it in your browser.")


@plugin.job("library.sources", "acquireParts")
def _acquire_parts(args, report):
    """Every part of one file host's split release as one acquire: each part's page opens in
    droidtop's web view in turn, the person goes through it, and the captured downloads go
    back together (`downloads`), marked to be joined and unpacked when they are one archive."""
    ref = args.get("ref") or {}
    url = str(ref.get("url") or "")
    site = site_of_url(url)
    group = str(args.get("group") or "")
    if site is None or not group:
        return gg.failed("Choose a file host first")
    r = release(site, url) or {}
    parts = part_members([o for o in r.get("options") or [] if o["group"] == group])
    if not parts:
        return gg.failed("That file host no longer lists the parts; open the release again")
    if len(parts) > gg.MAX_DOWNLOADS:
        return gg.failed(PARTS_TOO_MANY % len(parts))
    downloads = []
    for i, o in enumerate(parts, 1):
        report(int((i - 1) * 100 / len(parts)), "Part %d of %d: go through %s's page" % (i, len(parts), group))
        try:
            download = gg.open_in_session(o["link"])
        except gg.HostError as e:
            if e.code == "PERMISSION_DENIED":
                return gg.failed(SESSION_DENIED)
            raise
        if download is None:
            return gg.failed("Part %d of %d started no download; nothing was downloaded. Try again, or download the parts one by one" % (i, len(parts)))
        downloads.append(download)
    return gg.downloads_result("Downloading %s (%d parts)" % (r.get("name") or "the release", len(parts)), downloads)


# ------------------------------------------------------------------ library.updates (A6)


def parse_release_id(source, text):
    """A release page link (or its last path part) on `source`'s site -> (id, url)."""
    text = (text or "").strip()
    host = SITES[source]["host"]
    if source == "elamigos":
        m = re.search(r"(?:elamigos\.site/)?(?:data/)?([A-Za-z0-9_.()'+-]+\.html)$", text)
        return (m.group(1), "https://elamigos.site/data/" + m.group(1)) if m else (None, None)
    if text.startswith("http"):
        if site_of_url(text) != source:
            return None, None
        slug = slug_of(text)
    else:
        slug = text.strip("/")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,200}", slug or ""):
        return None, None
    return slug, "https://%s/%s/" % (host, slug)


def page_title(source, slug):
    """The release's current title and version from its page; None when the page is gone."""
    answer = gg.http("https://%s/%s/" % (SITES[source]["host"], slug))
    if answer.status in (404, 410):
        return None
    if not answer.ok:
        raise gg.HostError("FAILED", gg.http_error(SITES[source]["label"], answer.status))
    title = _title(answer.body)
    name, version = (split_fitgirl if source == "fitgirl" else split_dodi)(title)
    return {"title": title, "name": name, "version": version}


@plugin.on("library.updates", "resolve")
def _resolve(args):
    source = args.get("source")
    if source not in SITES:
        return gg.error("INVALID_ARGS", "Unknown source")
    rid, url = parse_release_id(source, args.get("text"))
    return gg.ok({"found": {"id": rid, "url": url}} if rid else {})


@plugin.on("library.updates", "match")
def _match(args):
    source = args.get("source")
    if source not in SITES:
        return gg.error("INVALID_ARGS", "Unknown source")
    title = str(args.get("title") or "")
    if not gg.words(title):
        return gg.ok({"candidates": []})
    found = search_elamigos(title) if source == "elamigos" else search_wordpress(source, title)
    key = gg.name_key(title)
    found.sort(key=lambda r: gg.name_key(r["name"]) != key)
    return gg.ok(
        {
            "candidates": [
                {k: v for k, v in {"id": r["id"], "title": r["name"], "version": r.get("version"), "url": r["url"], "note": r["title"]}.items() if v}
                for r in found[:20]
            ]
        }
    )


@plugin.on("library.updates", "check")
def _check(args):
    source = args.get("source")
    if source not in SITES:
        return gg.error("INVALID_ARGS", "Unknown source")
    if not settings()[source]:
        return gg.ok({"answers": []})  # turned off: every link keeps its last answer
    ids = [str(i) for i in (args.get("ids") or [])][:50]
    state = gg.read_json(STATE, {}) or {}
    seen = state.setdefault(source, {})
    answers = []
    news = []
    started = time.monotonic()
    by_file = {r["id"]: r for r in elamigos_list()} if source == "elamigos" else {}
    for rid in ids:
        if source == "elamigos":
            r = by_file.get(rid)
            if r is None:
                answers.append({"id": rid, "gone": True})
                continue
            current = {"name": r["name"], "version": r["version"]}
            url = r["url"]
        else:
            if time.monotonic() - started > CHECK_BUDGET_S:
                break  # the rest keep their last answer until the next round
            slug, url = parse_release_id(source, rid)
            if slug is None:
                continue
            current = page_title(source, slug)
            if current is None:
                answers.append({"id": rid, "gone": True})
                continue
        version = current.get("version")
        before = seen.get(rid)
        if version and before and before != version:
            news.append("%s: %s" % (current.get("name") or rid, version))
        if version:
            seen[rid] = version
        answer = {"id": rid, "url": url}
        if version:
            answer["version"] = version
        answers.append(answer)
    gg.write_json(STATE, state)
    if news:
        gg.notify("New %s release" % SITES[source]["label"] if len(news) == 1 else "%d new %s releases" % (len(news), SITES[source]["label"]), "\n".join(news[:8]))
    return gg.ok({"answers": answers})


# ------------------------------------------------------------------ settings (C)


def settings_view():
    s = settings()
    save = gg.call_action("save")
    return gg.view(
        "Repacks",
        [
            gg.toggle("fitgirl", "FitGirl", s["fitgirl"], save),
            gg.toggle("dodi", "DODI", s["dodi"], save),
            gg.toggle("elamigos", "ElAmigos", s["elamigos"], save),
        ],
    )


@plugin.on("ui.settings", "view")
def _settings(args):
    return gg.ok(settings_view())


@plugin.on("ui.settings", "save")
def _save(args):
    values = args.get("values") or {}
    s = settings()
    for key in SITES:
        if key in values:
            s[key] = str(values[key]).lower() == "true"
    gg.write_json(SETTINGS, s)
    return gg.ok({"view": settings_view()})


handle, start_job, cancel_job = plugin.entry_points()
