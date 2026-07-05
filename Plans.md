# MedOverflow Plans.md

Created: 2026-06-13

---

## Phase 0: M0 — Gate & foundations (v0.0.x) — BLOCKS ALL CODE

| Task | Content | DoD | Depends | Status |
|------|---------|-----|---------|--------|
| 0.1.1 | Decide native content license (CC BY-SA 4.0 Option A vs CC BY 4.0 Option B) | Decision ratified and documented in decision memo | - | cc:done [66de413] |
| 0.1.2 | Reject CC BY-NC (Option C) explicitly with rationale | Decision memo records why C is rejected (incompatible with SE mirroring) | 0.1.1 | cc:done [66de413] |
| 0.1.3 | Decide code license (AGPL-3.0 vs Apache-2.0 vs MIT) | Decision ratified with rationale for network-served commons argument | 0.1.1, 0.1.2 | cc:done [66de413] |
| 0.1.4 | Write `LICENSE` file (code license) | File exists at root, uses chosen code license with standard headers | 0.1.3 | cc:done [66de413] |
| 0.1.5 | Write `LICENSE-CONTENT.md` (content license choice + matrix) | File documents content license choice (A or B), per-source license matrix, rationale for choice | 0.1.1, 0.1.2, 0.1.3 | cc:done [66de413] |
| 0.2.1 | Define per-source license matrix | Documented: SE = CC BY-SA, Biostars = CC BY, FHIR Zulip = link-only | 0.1.1 | cc:done [ae7039f] |
| 0.2.2 | Write attribution rendering contract | Contract specifies: source + author + license + date + link always present in all render paths, non-strippable, test-enforced | 0.2.1 | cc:done [ae7039f] |
| 0.2.3 | ~~Define quarantine-partition rules (Option B, not chosen)~~ | Option A (CC BY-SA 4.0 uniform) was chosen; quarantine partition rejected. See LICENSE-CONTENT.md "Why CC BY-SA, not CC BY?" for rationale. | 0.1.1 | cc:done [ae7039f] |
| 0.3.1 | Create Cargo workspace stub | Cargo.toml root with workspace definition; four crates stubbed (`crates/qa-core/`, `crates/identity-verification/`, `crates/ingestion/`, `crates/search/`) with minimal Cargo.toml files; `cargo check` succeeds in root | - | cc:done [d3981dc] |
| 0.3.2 | Create pnpm workspace stub | Root `pnpm-workspace.yaml`, `web` package stubbed with `package.json` | - | cc:done [d3981dc] |
| 0.3.3 | Create uv project stub for ingestion | `ingestion/pyproject.toml` with uv marker, minimal deps stubbed | - | cc:done [d3981dc] |
| 0.3.4 | Configure CI (lint + semver + deny + typecheck) | CI runs: cargo fmt, cargo clippy -D warnings, cargo-semver-checks, cargo-deny, tsc --noEmit, ESLint, ruff+mypy | 0.3.1, 0.3.2, 0.3.3 | cc:done [d3981dc] |
| 0.3.5 | Implement architecture test harness | Test file created at `crates/qa-core/tests/architecture.rs`; test asserts zero imports of identity-verification, ingestion, search; test runs in CI on every push; CI fails if test fails | 0.3.1 | cc:done [d3981dc] |
| 0.4.1 | Draft on-topic scope definition | Document: clinical software/informatics/data IN; patient advice OUT; explicit moderation rules | - | cc:done [b0da321] |
| 0.4.2 | Write badge-semantics copy | UI copy clarifies: credential badge = engineering/informatics authority on software question, NOT clinical endorsement; patient advice out of scope | 0.4.1 | cc:done [b0da321] |

**M0 exit criterion:** Both content and code licenses chosen and written; CI is green on empty workspace; scope doc drafted and badge semantics clear.

---

## Phase 1: M1 — qa-core domain, library-only (v0.1.0)

| Task | Content | DoD | Depends | Status |
|------|---------|-----|---------|--------|
| 1.1.1 | Create `QuestionId`, `AnswerId`, `UserId` newtypes | Newtypes defined in qa-core, exhaustive pattern match enforced, type-safe constructors | Phase 0 | cc:done [001c288] |
| 1.1.2 | Create `Body` value object (non-empty, parsed) | `Body` type makes empty body unrepresentable; parser rejects empty/whitespace-only strings | 1.1.1 | cc:done [e63eebf] |
| 1.1.3 | Create `Tag` with date and jurisdiction facets | `Tag` enum includes `date` (YYYY-MM-DD) and `jurisdiction` fields; parser validates format | 1.1.1 | cc:done [88205a5] |
| 1.1.4 | Create `License` enum (CcBySa4, CcBy4, Native, LinkOnly) | Exhaustive enum with no catch-all; unknown license ⇒ parse error; compiler prevents catch-all | 1.1.1 | cc:done [b424c85] |
| 1.2.1 | Create `VerifiedCredential` opaque token (private constructor) | Constructor private to identity-verification crate; trybuild compile-fail test asserts qa-core cannot construct one | 1.1.1 | cc:done [b036c28] |
| 1.2.2 | Add `scope` (Clinical/Engineering/Research) and `expiry` to `VerifiedCredential` | Scope and expiry are first-class fields; typestate enforces valid lifecycle | 1.2.1 | cc:done [3df584b] |
| 1.2.3 | Implement `authority_weight()` as pure function of (scope, freshness) | Pure function computed from scope and expiry; no hidden state; deterministic on same inputs | 1.2.2 | cc:done [94e25cd] |
| 1.3.1 | Create `Question` aggregate with revision history | Aggregate includes `QuestionId`, `Body`, `author_id`, `created_at`, `revisions: Vec<Revision>` | 1.1.1, 1.1.2 | cc:done [e4f0874] |
| 1.3.2 | Create `Answer` aggregate with revision history and optional credential weight | Aggregate includes `AnswerId`, `Body`, `author_id`, `optional: VerifiedCredential`, `revisions`, `Vote` tracking | 1.1.1, 1.1.2, 1.2.1 | cc:done [368d30f] |
| 1.3.3 | Create `Vote` with `StillValid` variant | Vote enum: Helpful, Unhelpful, StillValid (perishability signal); StillValid count tracked per answer | 1.3.2 | cc:done [368d30f] |
| 1.4.1 | Define `CredentialPort` trait | Port: fn verify_credential(id: UserId) → Option<VerifiedCredential>; identity-verification implements | 1.2.1 | cc:done [ba55ea3] |
| 1.4.2 | Define `ContentSourcePort` trait | Port: fn source_license(id: ContentId) → License; ingestion implements per-source | 1.1.4 | cc:done [82578b6] |
| 1.4.3 | Define `SearchIndexPort` trait | Port: fn notify_content_changed(id); search projection subscribes | - | cc:done [f3836da] |
| 1.4.4 | Define `PersistencePort` trait | Port: fn persist(aggregate), fn retrieve(id); adapters for SQLite / Postgres | 1.3.1, 1.3.2 | cc:done [f79d21e] |
| 1.5.1 | Test: unknown license fails to parse | Test asserts License::parse("unknown") returns Err; exhaustive match enforced | 1.1.4 | cc:done [b424c85] |
| 1.5.2 | Test: qa-core cannot forge VerifiedCredential (trybuild compile-fail) | Compile-fail test asserts code VerifiedCredential::new(...) in qa-core does not compile | 1.2.1 | cc:done [f8580d3] |
| 1.5.3 | Architecture test: qa-core has zero outward deps | Test asserts qa-core crate depends only on std/proc-macro; no imports of identity-verification, ingestion, search | 1.4.1, 1.4.2, 1.4.3, 1.4.4 | cc:done [f79d21e] |

**M1 exit:** `qa-core` compiles as a library with zero outward deps; all invariants CI-enforced. No binary, no DB.

---

## Phase 2: M2 — Persistence + identity-verification (v0.2.0)

| Task | Content | DoD | Depends | Status |
|------|---------|-----|---------|--------|
| 2.1.1 | Create SQLite adapter for `PersistencePort` | Adapter: question/answer/vote persistence to SQLite; schema defined; all M1 aggregates round-trip | Phase 1 | cc:done [0f76652] |
| 2.1.2 | Create Postgres adapter for `PersistencePort` | Adapter: question/answer/vote persistence to Postgres; same schema; all M1 aggregates round-trip | 2.1.1 | cc:done [a2cc3d2] |
| 2.1.3 | Run conformance test suite against both adapters | Single test suite runs against SQLite and Postgres in parallel; all tests pass on both | 2.1.1, 2.1.2 | cc:done [b905dc1] |
| 2.2.1 | Create generic identity-verification adapter (ORCID + institutional email + manual review) | Adapter verifies ORCID, institutional email domain, manual review flag; issues VerifiedCredential with scope and expiry | - | cc:done [586058b] |
| 2.2.2 | Design Indonesia adapter (STR/KKI) — stub behind feature flag | Design document and stub implementation; feature flag controls activation; no external calls yet | - | cc:done [89e1c57] |
| 2.2.3 | Design US adapter (NPI) — stub behind feature flag | Design document and stub implementation; feature flag controls activation; no external calls yet | - | cc:done [89e1c57] |
| 2.2.4 | Implement credential expiry/lifecycle as typestate | Typestate prevents reading expired credentials; state machine: Issued → Active → Expired (linear) | 2.2.1 | cc:done [f11f20f] |
| 2.3 | Wire `CredentialPort` impl into qa-core via dependency injection | qa-core receives CredentialPort implementation at startup; answer authority weight computed via port; no hard dependency on identity-verification | Phase 1, 2.2.1, 2.2.4 | cc:done [ccdbf57] |

**M2 exit:** An answer can be persisted with or without verified credentials; works on SQLite and Postgres; badges carry scope+freshness weight.

---

## Phase 3: M3 — ingestion (license-aware bootstrap) (v0.3.0)

| Task | Content | DoD | Depends | Status |
|------|---------|-----|---------|--------|
| 3.1.1 | Create Stack Exchange dump parser (CC BY-SA, Python/uv) | Parser: reads SE dump format, emits parsed records with License::CcBySa4; attribution fields populated | Phase 2 | cc:done [c4a3888] |
| 3.1.2 | Create Biostars import adapter (CC BY) | Adapter: fetches/parses Biostars Q&A, emits records with License::CcBy4; attribution fields | 3.1.1 | cc:todo |
| 3.1.3 | Create FHIR Zulip adapter — link records only, assert no body copied | Adapter: emits link records (title + URL + metadata); asserts no body copy; all records have License::LinkOnly | 3.1.1 | cc:todo |
| 3.2.1 | Implement quarantine partition (if content license = Option B) | If CC BY 4.0 chosen: SA imports tagged with Quarantine::SaImport; rendering paths check partition boundary | Phase 0 (license choice), Phase 2 | cc:todo |
| 3.2.2 | Test: attribution rendering always includes source+author+license | Test: every rendered mirrored item includes source, author, license inline; test fails if any stripped | 3.1.1, 3.1.2, 3.1.3 | cc:todo |
| 3.2.3 | Implement topic filter: import only clinical-software-relevant items | Parser accepts only items tagged with clinical-software keywords (skip generic programming/non-clinical); filter configurable | 3.1.1 | cc:todo |

**M3 exit:** Corpus seeded from legally-mirrorable sources; every item correctly licensed and attributed; FHIR items are links only.

---

## Phase 4: M4 — search + read API (v0.4.0)

| Task | Content | DoD | Depends | Status |
|------|---------|-----|---------|--------|
| 4.1.1 | Wire `search` crate to qa-core's `SearchIndexPort` | `search` crate implements `SearchIndexPort`; depends on qa-core only (read-side); no write path back into qa-core | Phase 3 | cc:todo |
| 4.1.2 | Define index document schema | Index doc carries: kind (Q/A), body text, tags, jurisdiction, date, license, author, authority weight | 4.1.1 | cc:todo |
| 4.1.3 | Implement projection subscriber | `notify_content_changed(IndexableContent)` fetches the aggregate from persistence → upsert/delete index doc; idempotent on repeat notification | 4.1.1, 4.1.2 | cc:todo |
| 4.1.4 | Implement backfill/reproject path | Full index rebuild from persistence; idempotent and resumable; produces identical index to the incremental path | 4.1.3 | cc:todo |
| 4.2.1 | SQLite FTS5 full-text backend | Full-text backend on SQLite FTS5 (constrained single-binary path); indexes body + facets | 4.1.2 | cc:todo |
| 4.2.2 | Postgres tsvector full-text backend | Full-text backend on Postgres tsvector (hosted path); Tantivy deferred + documented | 4.1.2 | cc:todo |
| 4.2.3 | Shared conformance suite (both backends) | Single conformance suite runs against SQLite + Postgres; identical query results on both | 4.2.1, 4.2.2 | cc:todo |
| 4.3.1 | Parsed query input | Query type parses term + tag/jurisdiction/date filters; illegal query unrepresentable (Parse-Don't-Validate) | 4.2.3 | cc:todo |
| 4.3.2 | Facet counts | Query returns facet counts bucketed by tag × jurisdiction × date | 4.3.1 | cc:todo |
| 4.3.3 | Staleness surfacing | Date/jurisdiction facets flag stale answers; surfaced in query results | 4.3.2 | cc:todo |
| 4.3.4 | Deterministic ranking | Ranking = relevance × recency × authority weight; deterministic on same inputs; documented + tested | 4.3.1 | cc:todo |
| 4.4.1 | Read models (DTOs) | qa-core aggregates → serializable read DTOs; projection performs no writes into qa-core | 4.1.1 | cc:todo |
| 4.4.2 | Attribution non-strippable in read models | Every read model carries source+author+license+date+link; contract test fails if any stripped | 4.4.1 | cc:todo |
| 4.4.3 | Architecture test extension | Test asserts `search` crate has zero write path into qa-core (read-side only) | 4.1.1 | cc:todo |

**M4 exit:** content changes project into a dual-backend full-text index; faceted queries return tag×jurisdiction×date results that surface staleness; every mirrored result carries full attribution; search never writes to qa-core.

---

## Phase 5: M5 — web client, minimal (v0.5.0)

| Task | Content | DoD | Depends | Status |
|------|---------|-----|---------|--------|
| 5.1.1 | Client scaffold in `web` | pnpm workspace scaffolded; packages mirror domain boundaries; `pnpm exec tsc --noEmit` green | Phase 4 | cc:todo |
| 5.1.2 | Zod/Valibot at every I/O boundary | Schema validation on every request + response edge (Parse-Don't-Validate); invalid payload rejected at boundary | 5.1.1 | cc:todo |
| 5.1.3 | Branded id + discriminated-union types | Ids branded (QuestionId/AnswerId/UserId); `License` + `CredentialScope` as discriminated unions / `as const` | 5.1.1 | cc:todo |
| 5.1.4 | Typed API client | API client derived from read + write contracts; types flow end-to-end | 5.1.2, 5.1.3 | cc:todo |
| 5.2.1 | Ask flow | Ask (create question) form → API; validated at edge | 5.1.4 | cc:todo |
| 5.2.2 | Answer flow | Answer (create answer) form → API; validated at edge | 5.1.4 | cc:todo |
| 5.2.3 | Vote flow incl. `StillValid` | Vote buttons Helpful/Unhelpful/StillValid; StillValid perishability signal wired | 5.1.4 | cc:todo |
| 5.2.4 | Search + faceted browse | Search UI with tag × jurisdiction × date facets; calls the M4 query API | 5.1.4, 4.3.2 | cc:todo |
| 5.3.1 | Badge component | Badge rendered from authority scope + weight, on verified answers only | 5.1.3 | cc:todo |
| 5.3.2 | Non-dismissible safety copy | Copy: verification/engineering badge = software authority, NOT medical endorsement; non-dismissible | 5.3.1 | cc:todo |
| 5.3.3 | Test: badge safety invariants | Test: badge never renders as clinical advice; expired credential → no active badge | 5.3.1, 5.3.2 | cc:todo |
| 5.4.1 | Attribution component | Renders source + author + license + date + link inline; non-strippable | 5.1.1 | cc:todo |
| 5.4.2 | Test: attribution completeness | Test: every mirrored item renders all five fields; missing field ⇒ test fail | 5.4.1 | cc:todo |
| 5.4.3 | License-specific display | CC BY-SA / CC BY share-alike notice; `LinkOnly` renders link-out with no body copy | 5.4.1 | cc:todo |

**M5 exit:** a user can ask/answer/vote/search from the web client; ids and payloads are branded + schema-validated at every edge; credential badges carry non-dismissible safety copy; mirrored content always shows full attribution.

---

## Phase 6: M6 — Works → Community (v1.0.0 candidate)

| Task | Content | DoD | Depends | Status |
|------|---------|-----|---------|--------|
| 6.1.1 | Composition-root binary | Single binary wires qa-core + persistence-sqlite + identity-verification + search via DI | Phase 5 | cc:todo |
| 6.1.2 | SQLite-only single-binary build | Single Rust executable, embeds SQLite schema; no external services required | 6.1.1 | cc:todo |
| 6.1.3 | End-to-end smoke test | Smoke path: ask → answer → verify → search → attribution render, all in-binary | 6.1.2 | cc:todo |
| 6.1.4 | Release-profile CI green | `cargo-semver-checks` + `cargo-deny` green on the release profile | 6.1.2 | cc:todo |
| 6.2.1 | Publish community guidelines | On-topic/scope (from 0.4) published as community guidelines | Phase 0, 6.1.1 | cc:todo |
| 6.2.2 | Patient-advice-OUT boundary | Guidelines state the patient-advice-OUT boundary with worked examples | 6.2.1 | cc:todo |
| 6.2.3 | Attribution-preservation policy | Contribution policy documents CC BY-SA share-alike obligations + attribution preservation | 6.2.1 | cc:todo |
| 6.3.1 | Close/flag actions | Moderators can close/flag questions + answers | 6.1.1 | cc:todo |
| 6.3.2 | Patient-advice rejection path | Scope-boundary enforcement: patient-advice content rejected | 6.3.1, 6.2.2 | cc:todo |
| 6.3.3 | Moderation audit trail | Every moderation action recorded who / what / when | 6.3.1 | cc:todo |
| 6.4.1 | Release checklist | Every milestone exit met, CI green, licenses + attribution verified | 6.1.3, 6.1.4, 6.2.1, 6.3.1 | cc:todo |
| 6.4.2 | Tag v1.0.0 candidate | Version bumped + tagged v1.0.0 candidate; semver gate passes | 6.4.1 | cc:todo |
| 6.4.3 | Open to community | Publish community links; only after end-to-end demonstrably works | 6.4.1, 6.4.2 | cc:todo |

**M6 exit:** the single-binary SQLite deployment runs the full ask→answer→verify→search→attribute loop end-to-end; guidelines + moderation enforce the scope boundary; v1.0.0 opens to community only after it demonstrably works.

---

## Phase 7: Cross-cutting (every milestone)

| Task | Content | DoD | Depends | Status |
|------|---------|-----|---------|--------|
| 7.1 | Boy Scout Rule: leave touched modules cleaner than found | Guideline: no task leaves code worse than it found; applied to all code additions and refactors | - | cc:todo |
| 7.2 | Chesterton's Fence: keep deferred designs documented, not deleted | Guideline: deferred designs (decay/context-envelope, provenance graphs) remain in docs with rationale; never silently removed | - | cc:todo |
| 7.3 | SemVer discipline: `cargo-semver-checks` before each tag | Tooling: `cargo-semver-checks` runs in CI before release tags; tag creation fails if semver violation detected | 0.3.4 | cc:todo |
| 7.4 | Least privilege: each adapter gets only needed access | Design: adapters read-only where applicable; no adapter receives full system access; documented per adapter | - | cc:todo |
