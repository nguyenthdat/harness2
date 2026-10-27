# parse-standard-format-first

> Use standard, format-specific parsers (serde_json, url, csv, quick-xml, scraper) before ad-hoc string slicing or regex.

## Why It Matters

Structured formats such as JSON, URLs, CSV, XML, HTML, semantic versions, and HTTP syntax contain escaping, nesting, encoding, or normalization rules that ad-hoc splitting and regex commonly mishandle. Use a maintained, format-specific parser selected from repository dependencies and requirements. A parser does not by itself guarantee security: configure size/depth/entity/network limits, validate semantics after parsing, and preserve errors.

## Standard Parser Matrix

| Format / Domain | Candidate crate / standard type | Verify before choosing |
|-----------------|---------------------------------|------------------------|
| **JSON** | `serde_json` | numeric fidelity, recursion/input limits, typed schema |
| **URLs & URIs** | `url::Url`, `http::Uri` | WHATWG versus RFC semantics, allowed schemes/hosts |
| **HTTP syntax** | established HTTP stack, `httparse`, `http` types | framing ownership, header and byte limits |
| **CSV / Tabular** | `csv::ReaderBuilder` | delimiter/dialect, headers, record-size limits |
| **XML** | `quick-xml`, `roxmltree` | entity/DTD behavior, namespaces, depth and size limits |
| **HTML** | `scraper`, `html5ever` | HTML5 recovery semantics and input limits |
| **Semantic Versions** | `semver::Version` | repository versioning contract |
| **IP / Socket Addresses** | `std::net::IpAddr`, `std::net::SocketAddr` | policy validation beyond syntactic parsing |

## Bad

```rust
// Fragile ad-hoc URL extraction: breaks on userinfo, IPv6 hosts, query strings, and fragments
fn extract_domain(raw_url: &str) -> Option<&str> {
    if let Some(stripped) = raw_url.strip_prefix("https://") {
        stripped.split('/').next()
    } else if let Some(stripped) = raw_url.strip_prefix("http://") {
        stripped.split('/').next()
    } else {
        None
    }
}

// Fragile CSV parser: breaks on quotes containing commas, escaped quotes, and newlines
fn parse_csv_line(line: &str) -> Vec<&str> {
    line.split(',').map(|s| s.trim()).collect()
}
```

## Good

```rust
use url::Url;
use std::error::Error;

/// Safely parse and extract the domain from any valid URL scheme.
fn extract_domain(raw_url: &str) -> Result<String, Box<dyn Error>> {
    let parsed = Url::parse(raw_url)?;
    let host_str = parsed
        .host_str()
        .ok_or("URL missing host component")?;
    Ok(host_str.to_lowercase())
}

/// Robust RFC 4180 CSV record parsing with full support for quotes and escapes.
fn parse_csv_records<R: std::io::Read>(reader: R) -> Result<Vec<Vec<String>>, csv::Error> {
    let mut csv_reader = csv::ReaderBuilder::new()
        .has_headers(true)
        .trim(csv::Trim::All)
        .from_reader(reader);

    let mut results = Vec::new();
    for result in csv_reader.records() {
        let record = result?;
        results.push(record.iter().map(String::from).collect());
    }
    Ok(results)
}
```

## Structured JSON Deserialization

Always deserialize into strongly-typed structs rather than inspecting raw untyped strings or navigating manual dynamic values when the schema is known:

```rust
use serde::Deserialize;

#[derive(Debug, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct UserPayload {
    pub user_id: u64,
    pub email: String,
    pub is_active: bool,
    #[serde(default)]
    pub roles: Vec<String>,
}

pub fn parse_user_payload(raw_json: &str) -> Result<UserPayload, serde_json::Error> {
    serde_json::from_str(raw_json)
}
```

## Key Points

- Never parse structured web formats (URLs, query strings, cookies, headers) with regular expressions or `.split()`.
- Use `url::Url` for URL validation, path segment traversal, and query pair manipulation.
- Use `csv::Reader` for CSV data to handle embedded delimiters, multiline fields, and quotes correctly.
- Implement `std::str::FromStr` on domain types by delegating to standard parsers under the hood.
- For custom text protocols and DSLs without an established standard crate, use a formal grammar generator like `pest` (see `parse-pest-custom-grammar`).

## See Also

- [conv-fromstr-parsing](conv-fromstr-parsing.md) - implement `FromStr` for string-to-type parsing
- [api-parse-dont-validate](api-parse-dont-validate.md) - parse into validated types at boundaries
- [parse-pest-custom-grammar](parse-pest-custom-grammar.md) - use pest for non-trivial custom text grammars
- [parse-regex-simple-bounded](parse-regex-simple-bounded.md) - restrict regex to simple flat lexical patterns
