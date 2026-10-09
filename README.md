# droidtop-plugin-repacks

An **unofficial** plugin for [droidtop](https://github.com/Droidtop/droidtop) from
gamegrab-sources. It is not part of droidtop and is not affiliated with FitGirl,
DODI or ElAmigos.

## What it does

- **Get games** (droidtop's `library.sources`): searches the sites you turned on,
  from FitGirl's and DODI's own search pages and ElAmigos' release list (read once
  every 6 hours). Results show the site, the version and the size.
- **A release** shows what its page says (version, sizes, company, languages) and
  its download options:
  - **Torrents** (magnet links): droidtop has no torrent client, so **Open in a
    torrent app** hands the link to a torrent app you have installed.
  - **Direct links** (file hosts, and link pages such as filecrypt): the page opens
    in droidtop's browser view with this plugin's session; you go through the file
    host's page yourself (including any check it shows), and the download it starts
    runs in droidtop's Downloads into your game folder. A release in several parts
    needs every part downloaded into the same folder.
  - **Torrent file pages** (DODI): a file host page that gives a `.torrent` file
    opens in your browser.
- **Updates** (droidtop's `library.updates`): one source per site ("FitGirl
  release", "DODI release", "ElAmigos release"). Link a game to its release page
  and droidtop's update round reads the page's title for the current version (at
  most one page every 2 seconds per site); a notification says when a linked
  release has a new version.
- **Settings**: FitGirl, DODI and ElAmigos on or off. A site turned off is not
  searched or checked.

droidtop cannot yet open a link in another app; until it can, torrent and page
links are shown for you to copy.

## Permissions

- Connect to fitgirl-repacks.site, dodi-repacks.site and elamigos.site.
- Use your signed-in session on those sites (droidtop's browser view, for direct
  links; nothing is signed in).
- Notifications, and adding files to your game folders.

It runs contained in droidtop (no network or files of its own).

## Building

`./build.sh` writes `build/manifest.json` and `build/plugin.py` (the source with
the shared `gamegrab` module from the `common` submodule embedded); `./sign.sh`
signs and packs it. CI does both and publishes every working build of `main` as
a release; the gamegrab-sources catalog lists it from there. Tests:
`python3 common/test_gamegrab.py && python3 test_plugin.py`.

## Licence

GPL-3.0, see LICENSE and NOTICE.
