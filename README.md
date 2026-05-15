# beets-vocadb

Plugins for beets to use VocaDB, UtaiteDB and TouhouDB as autotagger sources.

## Installation

```sh
pip install git+https://github.com/prTopi/beets-vocadb
```

or, if you use [pipx](https://pipx.pypa.io):

```sh
pipx inject beets git+https://github.com/prTopi/beets-vocadb
```

This repository currently contains 3 plugins: `vocadb`, `utaitedb` and
`touhoudb`. To enable any of them, add the plugin name to the plugins section of
your beets config.

```yaml
plugins:
  - vocadb
  - utaitedb
  - touhoudb
```

## Subcommands

Each plugin adds a subcommand to beets that works similarly to the `mbsync`
command.

- VocaDB: `vdbsync`
- UtaiteDB: `udbsync`
- TouhouDB: `tdbsync`

For usage information run `beet [subcommand] -h`.

## Configuration

```yaml
 # Name of the plugin you want to configure (vocadb, utaitedb or touhoudb)
vocadb:
   # Penalty to be added to all matches with different source
   # when using autotagger (0 disabled, 1 highest)
  data_source_mismatch_penalty: 0.5
   # Number of results to get from source. Consider increasing
   # if the correct song or album doesn't show up in the list of candidates
  search_limit: 5
   # Prefer romanized if they exist rather than Japanese
  prefer_romaji: false
   # Include featured artists in album artists string
  include_featured_album_artists: false
   # When encountering a specific voicebank, replace it with it's
   # base voicebank (e. g. Hatsune Miku V4X (Original) -> Hatsune Miku)
  use_base_voicebank: false
   # List of fields that you do not want to see in the metadata of items.
  exclude_item_fields: []
   # Same as above, but for albums
  exclude_album_fields: []
```

The plugins use beets' default import language list to determine which language
to use for tags.

```yaml
import:
  # Example: Prefer Japanese language for tags
  languages:
    - jp
    - en
```

## FetchArt integration

The plugins integrate with [FetchArt](http://beets.readthedocs.org/en/latest/plugins/fetchart.html) using the flexible attribute field `cover_art_url`.
Refer to the [relevant section in it's documentation](https://beets.readthedocs.io/en/latest/plugins/fetchart.html#cover-art-url).

## Advanced configuration

Adding new sources is easy as long as the site is based on VocaDB.

A new source can be added by creating a new python file in the beetsplug folder
with a class that inherits from `beetsplug._utils.vocadb.PluginBase`
and passes the desired values to the required parameters. (see `utaitedb.py` or
`touhoudb.py` for reference.) The filename dictates the plugins name used for
configuration.

Feel free to create an issue or pull request about adding new sources.
