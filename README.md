# beets-vocadb

Plugin for beets to use VocaDB (or similar) as an autotagger source.

## Configuration

The plugin uses beets default language list to determine which language to use
for tags.

```yaml
vocadb:
  source_weight: 0.5    # Penalty to be added to all matches (0 disabled, 1 highest)
  import_lyrics: false  # Import lyrics to lyrics tag
  prefer_romaji: false  # Prefer romanized if they exist rather than Japanese
  no_empty_roles: false # Use producer(s) for arranger, composer and lyricist
                        # if the roles are not defined
```

### Advanced configuration

Source name and URLs can be changed inside the plugin source code in case
another site uses the same software as VocaDB

```python
VOCADB_NAME = "VocaDB"
VOCADB_BASE_URL = "https://vocadb.net/"
VOCADB_API_URL = "https://vocadb.net/api/"
```
