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

Torrent and page links open through Android's chooser; when that is not
possible (an older droidtop, the permission turned off, no app for the link)
they are shown to copy, with the reason. **Download all parts** fetches a file
host's numbered parts (up to 16) as one download into one folder: droidtop joins
and unpacks .7z.001-style parts and places .partN.rar volumes together for an app
that can unpack them.

## Permissions

- Connect to fitgirl-repacks.site, dodi-repacks.site and elamigos.site.
- Use your signed-in session on those sites (droidtop's browser view, for direct
  links; nothing is signed in).
- Notifications, and adding files to your game folders.
- Open links in other apps (magnets to your torrent app, pages to your browser).

It runs contained in droidtop (no network or files of its own).

## Building

`./build.sh` writes `build/manifest.json` and `build/plugin.py` (the source with
the shared `gamegrab` module from the `common` submodule embedded); `./sign.sh`
signs and packs it. CI does both and publishes every working build of `main` as
a release; the gamegrab-sources catalog lists it from there. Tests:
`python3 common/test_gamegrab.py && python3 test_plugin.py`.

## Licence

GPL-3.0, see LICENSE and NOTICE.

## Signing

The bundle carries `manifest.jws`: a detached ES256 JWS over the exact bytes of `manifest.json`, with this repository's leaf certificate in `x5c` (the root itself is not included). The leaf comes from the repository secrets `PLUGIN_SIGNING_KEY` and `PLUGIN_SIGNING_CERT` and was issued by the gamegrab root, a third-party anchor that people choose to trust (it is not pinned by the droidtop app); it names the plugin's origin and id. `sign_jws.py` writes the signature and checks it against the leaf before packing. `manifest.sig` stays in the bundle for older droidtop builds. Expiry dates are not checked.

`droidtop-plugin-key.json` in the repository root carries the gamegrab root certificate; droidtop reads it to anchor the `gamegrab` origin at that root.
