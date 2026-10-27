# parse-pest-custom-grammar

> Prefer an established parser for a standard format; for a new non-trivial custom grammar, evaluate `pest` against repository constraints and alternatives.

## Why It Matters

A declarative grammar can make custom DSL syntax, precedence, and error spans easier to review than accumulating splits and regexes. `pest` is one PEG option, not a universal default: handwritten parsers, `nom`, `winnow`, or another established project parser may better fit streaming, recovery, performance, allocation, or dependency constraints. PEG parsing also requires deliberate ambiguity and worst-case input analysis.

## Bad

```rust
// Fragile manual parser for key-value filter syntax like `user:alice AND age > 30`
// Misses nested parenthesis, operator precedence, escape sequences, and syntax errors
fn parse_filter(query: &str) -> Result<FilterAst, String> {
    let parts: Vec<&str> = query.split(" AND ").collect();
    // Manual string splitting collapses on whitespace variations, quoted values, etc.
    // Error positions and spans cannot be reliably reported to the user.
    todo!()
}
```

## Good

For production crates, define the formal grammar in a dedicated `.pest` file (such as `src/grammar/filter.pest`) and reference it with `#[grammar = "grammar/filter.pest"]`:

```pest
// Grammar definition: filter.pest
WHITESPACE = _{ " " | "\t" | "\r" | "\n" }

ident = @{ ASCII_ALPHA ~ (ASCII_ALPHANUMERIC | "_")* }
number = @{ ASCII_DIGIT+ }
string = { "\"" ~ (!"\"" ~ ANY)* ~ "\"" }

comparator = @{ "!=" | ">=" | "<=" | "=" | ">" | "<" }
comparison = { ident ~ comparator ~ (number | string | ident) }

expr = { comparison ~ (("AND" | "OR") ~ comparison)* }
query = { SOI ~ expr ~ EOI }
```

Derive the parser (using `#[grammar_inline = "..."]` for inline/self-contained modules or `#[grammar = "..."]` for external files) and build an Abstract Syntax Tree (AST) from Pest pairs with explicit error handling:

```rust
use pest::Parser;
use pest_derive::Parser;
use std::error::Error;

#[derive(Parser)]
#[grammar_inline = r#"
WHITESPACE = _{ " " | "\t" | "\r" | "\n" }

ident = @{ ASCII_ALPHA ~ (ASCII_ALPHANUMERIC | "_")* }
number = @{ ASCII_DIGIT+ }
string = { "\"" ~ (!"\"" ~ ANY)* ~ "\"" }

comparator = @{ "!=" | ">=" | "<=" | "=" | ">" | "<" }
comparison = { ident ~ comparator ~ (number | string | ident) }

expr = { comparison ~ (("AND" | "OR") ~ comparison)* }
query = { SOI ~ expr ~ EOI }
"#]
pub struct FilterParser;

#[derive(Debug, PartialEq, Eq)]
pub enum Operator {
    Eq,
    Neq,
    Gt,
    Gte,
    Lt,
    Lte,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Comparison {
    pub field: String,
    pub op: Operator,
    pub value: String,
}

#[derive(Debug, PartialEq, Eq)]
pub struct FilterQuery {
    pub comparisons: Vec<Comparison>,
}

pub fn parse_filter_query(input: &str) -> Result<FilterQuery, Box<dyn Error>> {
    let pairs = FilterParser::parse(Rule::query, input)?;
    let mut comparisons = Vec::new();

    for pair in pairs {
        if pair.as_rule() == Rule::query {
            for inner in pair.into_inner() {
                if inner.as_rule() == Rule::expr {
                    for cmp_pair in inner.into_inner() {
                        if cmp_pair.as_rule() == Rule::comparison {
                            let mut cmp_inner = cmp_pair.into_inner();
                            let field = cmp_inner
                                .next()
                                .ok_or("missing field identifier")?
                                .as_str()
                                .to_string();
                            let op_str = cmp_inner
                                .next()
                                .ok_or("missing comparator")?
                                .as_str()
                                .trim();
                            let val_str = cmp_inner
                                .next()
                                .ok_or("missing comparison value")?
                                .as_str();

                            let op = match op_str {
                                "=" => Operator::Eq,
                                "!=" => Operator::Neq,
                                ">" => Operator::Gt,
                                ">=" => Operator::Gte,
                                "<" => Operator::Lt,
                                "<=" => Operator::Lte,
                                other => return Err(format!("unexpected operator: {other}").into()),
                            };

                            comparisons.push(Comparison {
                                field,
                                op,
                                value: val_str.trim_matches('"').to_string(),
                            });
                        }
                    }
                }
            }
        }
    }

    Ok(FilterQuery { comparisons })
}
```

## Rich Spanned Error Reporting

`pest` automatically generates readable, formatted compile-like errors with exact line numbers, columns, and visual carets when parsing fails:

```text
 --> 1:19
  |
1 | age >= 30 AND status == "active"
  |                      ^---
  |
  = expected comparator (one of: '!=', '>=', '<=', '=', '>', '<')
```

## Key Points

- Prefer the repository's established parser and dependencies; justify any new parser crate.
- For `pest`, keep grammar rules bounded, audit ordered-choice behavior, and convert generated pairs into a typed AST with explicit error handling.
- Use silent or atomic rules only when their whitespace and backtracking semantics match the grammar.
- Match generated `Rule` variants deliberately; do not replace parser errors with `unwrap()` or unchecked `unreachable!()` assumptions.
- For established structured formats, use maintained format-specific parsers before defining a custom grammar.

## See Also

- [parse-standard-format-first](parse-standard-format-first.md) - prefer standard format parsers for JSON, URL, CSV
- [parse-regex-simple-bounded](parse-regex-simple-bounded.md) - reserve regex for flat lexical tokens only
- [api-parse-dont-validate](api-parse-dont-validate.md) - transform unparsed input into validated domain types
- [err-custom-type](err-custom-type.md) - define typed error categories for parse failures
