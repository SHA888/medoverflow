# TODO — atomic backlog

SemVer-milestoned. Tasks are atomic; subtasks are the smallest reviewable unit.
Nothing in M1+ starts until **M0** closes (the LICENSE gate). Order is
Bootstrap → Works → Community.

Legend: `[ ]` todo · `[~]` in progress · `[x]` done

---

## M0 — Gate & foundations (v0.0.x) — BLOCKS ALL CODE

- [x] **0.1 Settle content LICENSE** (README options A/B/C)
  - [x] 0.1.1 Decide native content license (A: CC BY-SA 4.0 | B: CC BY 4.0 + quarantine)
  - [x] 0.1.2 Reject C (CC BY-NC) explicitly — incompatible with SE mirroring; record rationale
  - [x] 0.1.3 Decide code license (AGPL-3.0 vs Apache-2.0 vs MIT); record rationale
  - [x] 0.1.4 Write `LICENSE` (code) and `LICENSE-CONTENT.md` (corpus)
- [x] **0.2 Legal/attribution spec**
  - [x] 0.2.1 Per-source license matrix (SE = CC BY-SA, Biostars = CC BY, FHIR Zulip = link-only)
  - [x] 0.2.2 Attribution rendering contract (source + author + license, non-strippable)
  - [x] 0.2.3 If Option B: quarantine-partition rules for SA content
- [x] **0.3 Repo & CI skeleton** (no domain code yet)
  - [x] 0.3.1 Cargo workspace stub; `cargo install cargo-skill`
  - [x] 0.3.2 pnpm workspace stub
  - [x] 0.3.3 uv project stub for ingestion
  - [x] 0.3.4 CI: fmt, clippy `-D warnings`, `tsc --noEmit`+ESLint, ruff+mypy, `cargo-semver-checks`, `cargo-deny`
  - [x] 0.3.5 Architecture test harness (asserts qa-core has no outward deps)
- [x] **0.4 On-topic / scope definition** (the patient-safety boundary, in prose)
  - [x] 0.4.1 Draft on-topic rules (clinical software/informatics/data IN; patient advice OUT)
  - [x] 0.4.2 Badge-semantics copy (engineering authority ≠ clinical endorsement)

**M0 exit criterion:** both licenses chosen and written; CI is green on an empty workspace; scope doc drafted.

---

## M1 — qa-core domain, library-only (v0.1.0)

- [x] **1.1 Core value objects (Parse-Don't-Validate)**
  - [x] 1.1.1 `QuestionId`/`AnswerId`/`UserId` newtypes
  - [x] 1.1.2 `Body` (non-empty, parsed) — empty body unrepresentable
  - [x] 1.1.3 `Tag` with `date` and `jurisdiction` facets
  - [x] 1.1.4 `License` enum (`CcBySa4`,`CcBy4`,`Native`,`LinkOnly`); unknown ⇒ parse error
- [x] **1.2 `VerifiedCredential` value object**
  - [x] 1.2.1 Opaque token; constructor private to verification crate (compile-fail test via trybuild)
  - [x] 1.2.2 `scope` (Clinical/Engineering/Research) + `expiry`
  - [x] 1.2.3 `authority_weight()` as pure fn of (scope, freshness)
- [x] **1.3 Aggregates**
  - [x] 1.3.1 `Question` with revision history
  - [x] 1.3.2 `Answer` with revision history + optional credential weight
  - [x] 1.3.3 `Vote` incl. `StillValid` variant (perishability signal)
- [x] **1.4 Ports (traits) defined in qa-core**
  - [x] 1.4.1 `CredentialPort`
  - [x] 1.4.2 `ContentSourcePort`
  - [x] 1.4.3 `SearchIndexPort`
  - [x] 1.4.4 `PersistencePort`
- [x] **1.5 Invariant tests**
  - [x] 1.5.1 unknown-license-fails-to-parse
  - [x] 1.5.2 core-cannot-forge-credential (trybuild compile-fail)
  - [x] 1.5.3 architecture test: no outward deps from qa-core

**M1 exit:** `qa-core` compiles as a library with zero outward deps; invariants CI-enforced. No binary, no DB.

---

## M2 — Persistence + identity-verification (v0.2.0)

- [x] **2.1 PersistencePort adapters**
  - [x] 2.1.1 SQLite adapter (constrained single-binary path)
  - [x] 2.1.2 Postgres adapter (hosted path)
  - [x] 2.1.3 Shared conformance test-suite run against both
- [x] **2.2 identity-verification crate**
  - [x] 2.2.1 Generic adapter (ORCID + institutional email + manual review)
  - [x] 2.2.2 Indonesia adapter (STR/KKI) — design + stub behind feature flag
  - [x] 2.2.3 US adapter (NPI) — design + stub behind feature flag
  - [x] 2.2.4 Credential expiry/lifecycle as typestate
- [x] **2.3 Wire `CredentialPort` impl into qa-core via DI**

**M2 exit:** an answer can be persisted and, if its author is verified, carry a badge+weight; works on SQLite and Postgres.

---

## M3 — ingestion (license-aware bootstrap) (v0.3.0)

- [ ] **3.1 `ContentSourcePort` adapters**
  - [ ] 3.1.1 Stack Exchange dump parser (CC BY-SA) — Python/uv, emits parsed records
  - [ ] 3.1.2 Biostars import (CC BY)
  - [ ] 3.1.3 FHIR Zulip adapter — **link records only**, asserts no body copied
- [ ] **3.2 License enforcement**
  - [ ] 3.2.1 Quarantine partition (only if content license = Option B)
  - [ ] 3.2.2 Attribution rendering test (source+author+license always present)
  - [ ] 3.2.3 Topic filter: only clinical-software-relevant items imported (not all of SO)

**M3 exit:** corpus seeded from legally-mirrorable sources, every item correctly licensed and attributed; FHIR items are links, not copies.

---

## M4 — search + read API (v0.4.0)

- [ ] **4.1 `search` crate + projection wiring**
  - [ ] 4.1.1 Wire `search` crate to qa-core's `SearchIndexPort` (read-side; depends on qa-core only, no write path back)
  - [ ] 4.1.2 Index document schema (kind, body text, tags, jurisdiction, date, license, author, authority weight)
  - [ ] 4.1.3 Projection subscriber: `notify_content_changed(IndexableContent)` → fetch aggregate from persistence → upsert/delete doc (idempotent)
  - [ ] 4.1.4 Backfill/reproject path: rebuild full index from persistence (idempotent, resumable)
- [ ] **4.2 `SearchIndexPort` full-text backends (dual, mirrors persistence split)**
  - [ ] 4.2.1 SQLite FTS5 backend (constrained single-binary path)
  - [ ] 4.2.2 Postgres tsvector backend (hosted path); Tantivy deferred + documented
  - [ ] 4.2.3 Shared conformance suite run against both backends
- [ ] **4.3 Faceted read query**
  - [ ] 4.3.1 Parsed query input (term + tag/jurisdiction/date filters); illegal query unrepresentable
  - [ ] 4.3.2 Facet counts: tag × jurisdiction × date buckets
  - [ ] 4.3.3 Staleness surfacing via date/jurisdiction facets
  - [ ] 4.3.4 Deterministic ranking (relevance × recency × authority weight); documented + tested
- [ ] **4.4 Read-side integrity**
  - [ ] 4.4.1 Read models: qa-core aggregates → serializable DTOs (no writes to qa-core)
  - [ ] 4.4.2 Attribution non-strippable in every read model (source+author+license+date+link) — contract test
  - [ ] 4.4.3 Architecture test extension: `search` has zero write path into qa-core

**M4 exit:** content changes project into a dual-backend full-text index; faceted queries return tag×jurisdiction×date results that surface staleness; every mirrored result carries full attribution; search never writes to qa-core.

---

## M5 — web client, minimal (v0.5.0)

- [ ] **5.1 pnpm client scaffold + typed API edges**
  - [ ] 5.1.1 Client scaffold in `web` (pnpm workspace mirrors domain boundaries)
  - [ ] 5.1.2 Zod/Valibot schemas at every I/O boundary (request + response), Parse-Don't-Validate
  - [ ] 5.1.3 Branded id types (QuestionId/AnswerId/UserId); discriminated unions for `License` + `CredentialScope`
  - [ ] 5.1.4 Typed API client derived from the read + write contracts
- [ ] **5.2 Core flows**
  - [ ] 5.2.1 Ask (create question)
  - [ ] 5.2.2 Answer (create answer)
  - [ ] 5.2.3 Vote incl. `StillValid` perishability signal
  - [ ] 5.2.4 Search + faceted browse (tag × jurisdiction × date)
- [ ] **5.3 Credential badge rendering**
  - [ ] 5.3.1 Badge component from authority scope + weight
  - [ ] 5.3.2 Safety copy: verification/engineering badge ≠ medical endorsement (non-dismissible)
  - [ ] 5.3.3 Test: badge never renders as clinical advice; expired credential → no active badge
- [ ] **5.4 Attribution rendering (mirrored content)**
  - [ ] 5.4.1 Attribution component: source + author + license + date + link (non-strippable)
  - [ ] 5.4.2 Test: every mirrored item renders all five fields; missing field ⇒ test fail
  - [ ] 5.4.3 License-specific display (CC BY-SA / CC BY share-alike notice; `LinkOnly` = link-out, no body copy)

**M5 exit:** a user can ask/answer/vote/search from the web client; ids and payloads are branded + schema-validated at every edge; credential badges carry non-dismissible safety copy; mirrored content always shows full attribution.

---

## M6 — Works → Community (v1.0.0 candidate)

- [ ] **6.1 Single-binary self-host path**
  - [ ] 6.1.1 Composition-root binary: qa-core + persistence-sqlite + identity-verification + search wired via DI
  - [ ] 6.1.2 SQLite-only single-binary build (no external services)
  - [ ] 6.1.3 End-to-end smoke: ask → answer → verify → search → attribution render
  - [ ] 6.1.4 Release-profile CI green: `cargo-semver-checks` + `cargo-deny`
- [ ] **6.2 Community guidelines**
  - [ ] 6.2.1 Publish on-topic/scope (from 0.4) as community guidelines
  - [ ] 6.2.2 Patient-advice-OUT boundary with worked examples
  - [ ] 6.2.3 Contribution + attribution-preservation policy (CC BY-SA share-alike obligations)
- [ ] **6.3 Moderation tooling**
  - [ ] 6.3.1 Close/flag actions on questions + answers
  - [ ] 6.3.2 Patient-advice rejection path (scope-boundary enforcement)
  - [ ] 6.3.3 Moderation audit trail (who / what / when)
- [ ] **6.4 Launch gate**
  - [ ] 6.4.1 Release checklist: every milestone exit met, CI green, licenses + attribution verified
  - [ ] 6.4.2 Tag v1.0.0 candidate
  - [ ] 6.4.3 **Only now**: open to community — only after end-to-end demonstrably works

**M6 exit:** the single-binary SQLite deployment runs the full ask→answer→verify→search→attribute loop end-to-end; guidelines + moderation enforce the scope boundary; v1.0.0 opens to community only after it demonstrably works.

---

## Cross-cutting (every milestone)

- [ ] Boy Scout Rule: leave touched modules cleaner than found
- [ ] Chesterton's Fence: deferred designs (decay/context-envelope) stay documented, not deleted
- [ ] SemVer discipline: `cargo-semver-checks` gate before each tagged release
- [ ] Least privilege: each adapter gets only the access it needs
