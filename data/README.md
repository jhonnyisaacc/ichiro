# data

Raw and derived market data are not committed. Only manifests are.

- `manifests/<dataset>.json`: source, markets, date range, row count, schema version, and sha256 of each file.
- `raw/` and `derived/`: local or external storage, ignored by git. See the layout in [data-infrastructure.md](../docs/data-infrastructure.md).

Anything over about 1 MB goes to external storage, with its manifest committed here.
