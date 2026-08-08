# Archive

Superseded material, kept for reference. **Nothing here is used by the current
app.** Moved out of the project root on 2026-08-03 so the old vector database
could not be picked up by mistake.

| Folder | What it holds | Why it is here |
|---|---|---|
| `old_vector_database/` | `chroma_db/` (345 MB) and `chroma_db.zip` (175 MB) | The first-generation index: 32,177 chunks, MiniLM embeddings, collection `geotech_docs`. Replaced by `data/chroma` + `data/tdg_text.sqlite` (499,071 chunks, bge-small embeddings, hybrid vector + keyword search). |
| `old_pdf_library/` | `PDF_database/` (1.2 GB) | Source PDFs the corpus was extracted from. The app reads the Markdown in `data/TDG_GEOTECHNICAL_DATABASE` instead. Copyrighted: keep out of any public repository. |
| `old_ingestion_environment/` | `ingestion_env/` (1.2 GB) | Standalone virtualenv used for the original PDF extraction. Ingestion now runs from the project `.venv`. |
| `unrelated_projects/` | `From_benchmark_project/` | Files from a different project. |
| `old_outputs/` | `outputs/` | Generated artifacts from earlier runs. |

## Restoring something

Move the folder back to the project root, e.g.:

    Move-Item archive\old_vector_database\chroma_db .\chroma_db

Note on classic mode: the legacy multi-agent path (`/ask` and the frontend's
`?classic=1`) read `./chroma_db`. With that database archived, classic mode has
no local index and its retrieval returns nothing; the brain skips the
re-download and logs a notice instead. Ask mode (the current tutor) is
unaffected, and the deployed Railway service still downloads its own copy.
