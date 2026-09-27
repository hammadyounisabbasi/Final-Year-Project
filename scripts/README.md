# Maintenance Scripts

Run scripts from the repository root with the active Python environment.

## Database provisioning

`setup_database.py` atomically builds SQLite from the versioned schemas, optional demo seeds, migrations, corrected trigger set, and views.

```bash
python scripts/setup_database.py
```

It refuses to overwrite an existing database. Use `--force` only for a deliberate rebuild, `--without-seed` for an empty schema, or `--database PATH` for a disposable/test database.

## Focused maintenance

- `apply_timetable_migration.py` applies the timetable migration workflow to an existing development database.
- `build_fee_knowledge.py` rebuilds the deterministic fee knowledge artifacts.

Back up persistent data before running maintenance against a deployed environment. Never commit generated databases, uploaded documents, logs, or indexes.

The project does not ship model-download or FAISS-initialization helpers. Install local Ollama models through the Ollama CLI. Timetable retrieval defaults to its built-in hash embedding provider; the optional sentence-transformers provider is selected through `.env`.
