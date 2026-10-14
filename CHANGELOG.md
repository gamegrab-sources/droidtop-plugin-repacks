# Changelog

Every working build of `main` is a release (`v<version>-<CI run>`); the
declared version moves with every change to the plugin's sources.

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
