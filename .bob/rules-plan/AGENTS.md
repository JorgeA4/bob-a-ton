# AGENTS.md — Plan mode

This file provides guidance to agents when working with code in this repository.

## Architectural constraints

- **Strict layer separation:** Dev B (`ai/`) never parses JSON; Dev C (`core/`) never calls Gemini. Crossing this boundary breaks the integration contract.
- **Single data model:** `Ubicacion` and `Criterio` dataclasses are the only shared data types; any new field must be added here and reflected in the `AI_INSTRUCTIONS.md` prompt schema simultaneously.
- **Gemini model is fixed:** `gemini-1.5-flash` — do not plan around other models without updating the client.
- **No database:** all data is ephemeral per Streamlit session; no persistence layer is planned for fase 1.
- Dev A integrates last and should use mock `List[Ubicacion]` objects while Dev B/C are in progress.
