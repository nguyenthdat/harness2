---
name: structured-parsing
description: Prefer typed structural parsers over regex for JSON, HTML, XML, URLs, source code, protocols, and other nested formats.
---

# Structured Parsing

Apply whenever code parses, edits, validates, or extracts structured text.

1. Use the language standard library or the repository's established parser for the format: JSON decoder, HTML/XML DOM or tokenizer, URL parser, CSV parser, compiler AST, protocol/schema runtime, or equivalent.
2. Use a maintained format-specific library when the standard library has no correct parser. Preserve source locations and parser errors when diagnostics matter.
3. Use regex only for flat regular tokens or bounded local extraction, or when a structural parser is unavailable/inapplicable and the limitation is explicit. Anchor the pattern, bound input and repetition, avoid catastrophic backtracking, and test adversarial cases.
4. Never parse nested, escaped, recursive, context-sensitive, or security-relevant formats with regex when a structural parser exists.
5. Parse into typed values at the boundary. Do not pass stringly-typed structure through core logic.