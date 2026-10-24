# Changelog

Every working build of `main` is a release (`v<version>-<CI run>`); the
declared version moves with every change to the plugin's sources.

## 0.6.0

- `featured` lists FitGirl's and DODI's newest releases too, from their home pages, beside ElAmigos': taken from each
  site turned on in turn, newest first within each, so every site shows near the top of droidtop's Get new games. A
  pinned post, an updates digest, the "Upcoming Repacks" page and a DODI site notice are left out; a site that cannot
  be read now is left out, and only with none read does `featured` fail. The home pages are bigger than one answer, so
  they come through `net.download` when cut (Droidtop/tracker#612).
- DODI's list pages are read by their `entry-title` on an h3 too, as DODI's home page has it.

## 0.5.0

- `featured` (droidtop docs/plugin-api.md 1.8, Droidtop/tracker#612): ElAmigos' newest releases, in the order its
  home page lists them, at most the `limit` droidtop asks for (up to 60), for droidtop's Get new games page, while
  ElAmigos is turned on. FitGirl and DODI are not listed there yet. A console's page gets none.

## 0.4.1

- The release of 0.4.0's facets and contract 3 changes. 0.4.0's two commits shared one declared version, so CI's version rule refused the second
  and 0.4.0 was never released; this version carries both unchanged.

## 0.4.0

- The settings are `settings.page` facets (droidtop docs/plugin-api.md 1.10) in place of the `ui.settings` view: a
  switch per site, each saved on its own as it is turned (`setSite`, with droidtop's `value`).
- The manifest says `"contractVersion": 3`: it needs facets, so a droidtop built before them refuses this version
  and keeps the one installed, rather than install a plugin whose settings it cannot draw (droidtop docs/plugin-api.md
  7, "Contract 3").

## 0.3.2

- Names its kind for droidtop's Plugins page (`category`, docs/plugin-api.md 1.2, Droidtop/tracker#179).

## 0.3.1

- Declares the systems it serves (Windows), so droidtop lists it in PC searches and not under a console such as Game Boy Advance.
  Needs a droidtop that reads `systems` on `library.sources` (docs/plugin-api.md 1.6); an older
  droidtop ignores the field and lists the source everywhere, as before.

## 0.3.0

- Failures in plain words ("FitGirl is not answering right now") instead of
  "answered HTTP 503".
- Shorter text: one-line description (the catalog marks the plugin
  Unofficial), one-line hints for direct links, parts and torrents, no note
  rows in Settings.
- Shared module 0.3.0 (contract 2.1 host names, needs droidtop
  0.2.0-dev.1767 or newer; smaller data reads).

## 0.2.0

- Torrents, release pages and DODI torrent-file pages open through
  Android's chooser (droidtop's apps.view, permission "Open links in other
  apps"); the link is shown to copy only when that is not possible, with
  the reason.
- Download all parts: a file host's numbered parts (up to 16) go through
  droidtop's browser view one after another and come back as one download
  (acquire `downloads`) into one folder; droidtop joins and unpacks
  .7z.001-style parts and places .partN.rar volumes together (it does not
  unpack split RAR files yet).

## 0.1.0

- First version: FitGirl, DODI and ElAmigos in one plugin with a toggle per
  site. Get games searches them; a release's page lists its torrents (handed to
  a torrent app) and direct links (opened in droidtop's browser view, the
  download running in droidtop's Downloads); a game linked to a release page is
  checked for new versions, with a notification.
