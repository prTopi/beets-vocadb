# beets-vocadb

Plugin for beets to use VocaDB, UtaiteDB and TouhouDB as an autotagger source.

## Installation

```Shell
pip install git+https://github.com/prTopi/beets-vocadb
```

or, if you use [pipx](https://pipx.pypa.io):

```Shell
pipx inject beets git+https://github.com/prTopi/beets-vocadb
```

This Plugin has 3 components: vocadb, utaitedb and touhoudb.
To enable them, add them to the plugin section of your beets config file:

```yaml
plugins:
  - vocadb
  - utaitedb
  - touhoudb
```

## Configuration

The plugin uses beets default language list to determine which language to use
for tags.

```yaml
vocadb:
  source_weight: 0.5    # Penalty to be added to all matches (0 disabled, 1 highest)
  prefer_romaji: false  # Prefer romanized if they exist rather than Japanese
  translated_lyrics: false  # Always get translated lyrics if they're available
```

utaitedb and touhoudb have the same configuration options.

### Advanced configuration

If you want to use another site based on VocaDB, create another .py file in the beetsplug directory.
Look at utaitedb.py and touhoudb.py for reference
