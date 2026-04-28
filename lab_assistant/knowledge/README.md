# Knowledge Pipeline

Purpose:
- Turn historical lab summaries and field papers into reusable scientific context.

Design goals:
- explicit provenance
- compact, high-signal notes
- easy expansion as the NAS finishes syncing
- clean separation between raw extraction, paper shelf, and synthesis notes

Structure:
1. `sources/`
- declarative roots for decks, papers, and notes on the NAS
2. `index/`
- deterministic inventories with stable metadata
3. `extracted/`
- machine-readable text for documents worth mining further
4. `papers/`
- growing paper shelf organized by topic, with short result-centered annotations
5. `syntheses/`
- higher-level topic notes that compress the field and cite into `papers/`
6. `projects/`
- project-facing notes that link active Xu Lab work to the relevant syntheses, papers, and canon
7. `canon/`
- compact collection notes, lab-history notes, and other durable local context

Core scripts:
- `scripts/build_reference_inventory.py`
- `scripts/extract_reference_text.py`
- `scripts/build_reference_overview.py`
- `knowledge/run_refresh.sh`

Recommended operating loop:
1. refresh inventory
2. extract text for newly discovered files
3. add important papers to `papers/`
4. update topic syntheses with only the durable conclusions
5. promote stable lab-specific patterns into `canon/` and `context/`

Working rule:
- maintain breadth in `papers/`
- maintain compression in `syntheses/`
- maintain navigability in `projects/`
- avoid turning syntheses into giant bibliographies or decision trees
- make it easy to enter the knowledge base either by project or by scientific domain
