# beets-vocadb

Plugins for beets to use VocaDB, UtaiteDB and TouhouDB as autotagger sources.

## Installation

```Shell
pip install git+https://github.com/prTopi/beets-vocadb
```

or, if you use [pipx](https://pipx.pypa.io):

```Shell
pipx inject beets git+https://github.com/prTopi/beets-vocadb
```

This repository contains 3 plugins: vocadb, utaitedb and touhoudb.
To enable them, add them to the plugin section of your beets config file:

```yaml
plugins:
  - vocadb
  - utaitedb
  - touhoudb
```

## Subcommands

Each plugin adds a subcommand to beets that works similarly to the mbsync command.
vocadb adds `vdbsync`, utaitedb adds `udbsync` and touhoudb adds `tdbsync`.
For usage information run `beet [subcommand] -h`.

## Configuration

The plugins use beets default language list to determine which language to use
for tags.

```yaml
vocadb:
  source_weight: 0.5    # Penalty to be added to all matches (0 disabled, 1 highest)
  prefer_romaji: false  # Prefer romanized if they exist rather than Japanese
  translated_lyrics: false  # Always get translated lyrics if they're available
```

utaitedb and touhoudb have the same configuration options.

## Advanced configuration

If you want to use another site based on VocaDB, create another .py file in the beetsplug directory.
Look at utaitedb.py and touhoudb.py for reference
