# beets-vocadb

Plugins for beets to use VocaDB, UtaiteDB and TouhouDB as autotagger sources.

## Maintenance mode

The main branch of this plugin is mainly in maintenance mode, and won't receive
major changes.

If you wish to use a more complex version of the plugin with numerous
improvements, check out the
[experimental branch](https://github.com/prTopi/beets-vocadb/tree/experimental).

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

The other plugins (utaitedb and touhoudb) will use the same settings as vocadb
as a fallback, so you don't have to repeat yourself. (except for
`data_source_mismatch_penalty` and `search_limit`)

```yaml
vocadb: # Name of the plugin you want to configure (vocadb, utaitedb or touhoudb)
  data_source_mismatch_penalty: 0.5 # Penalty to be added to all matches with different source when using autotagger (0 disabled, 1 highest)
  search_limit: 5 # Number of results to get from source. Consider increasing if correct song or album doesn't show up in the list of candidates
  prefer_romaji: false # Prefer romanized if they exist rather than Japanese
  translated_lyrics: false # Always get translated lyrics if they're available
  include_featured_album_artists: false # Include featured artists in album artists string
  va_string: "Various artists" # Album artist name to use when artist list contains many artists
```

The plugins use beets' default import language list to determine which language
to use for tags. (English is used as a fallback)

```yaml
import:
  languages: # Example: Prefer Japanese language for tags
    - jp
    - en
```

## Advanced configuration

Adding new sources is easy as long as the site is based on VocaDB.

A new source can be added by creating a new python file in the beetsplug folder
with a class that inherits classes `VocaDBPlugin` and `VocaDBInstance` with the
instance information (see `utaitedb.py` or `touhoudb.py` for reference.) The
filename dictates the plugins name used for configuration.

Feel free to create an issue or pull request about adding new sources.
