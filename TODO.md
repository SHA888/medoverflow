# TODO — atomic backlog

SemVer-milestoned. Tasks are atomic; subtasks are the smallest reviewable unit.
Nothing in M1+ starts until **M0** closes (the LICENSE gate). Order is
Bootstrap → Works → Community.

Legend: `[ ]` todo · `[~]` in progress · `[x]` done

---

## M0 — Gate & foundations (v0.0.x) — BLOCKS ALL CODE

- [ ] **0.1 Settle content LICENSE** (README options A/B/C)
  - [ ] 0.1.1 Decide native content license (A: CC BY-SA 4.0 | B: CC BY 4.0 + quarantine)
  - [ ] 0.1.2 Reject C (CC BY-NC) explicitly — incompatible with SE mirroring; record rationale
  - [ ] 0.1.3 Decide code license (AGPL-3.0 vs Apache-2.0 vs MIT); record rationale
  - [ ] 0.1.4 Write `LICENSE` (code) and `LICENSE-CONTENT.md` (corpus)
- [ ] **0.2 Legal/attribution spec**
  - [ ] 0.2.1 Per-source license matrix (SE = CC BY-SA, Biostars = CC BY, FHIR Zulip = link-only)
  - [ ] 0.2.2 Attribution rendering contract (source + author + license, non-strippable)
  - [ ] 0.2.3 If Option B: quarantine-partition rules for SA content
- [ ] **0.3 Repo & CI skeleton** (no domain code yet)
  - [ ] 0.3.1 Cargo workspace stub; `cargo install cargo-skill`
  - [ ] 0.3.2 pnpm workspace stub
  - [ ] 0.3.3 uv project stub for ingestion
  - [ ] 0.3.4 CI: fmt, clippy `-D warnings`, `tsc --noEmit`+ESLint, ruff+mypy, `cargo-semver-checks`, `cargo-deny`
  - [ ] 0.3.5 Architecture test harness (asserts qa-core has no outward deps)
- [ ] **0.4 On-topic / scope definition** (the patient-safety boundary, in prose)
  - [ ] 0.4.1 Draft on-topic rules (clinical software/informatics/data IN; patient advice OUT)
  - [ ] 0.4.2 Badge-semantics copy (engineering authority ≠ clinical endorsement)

**M0 exit criterion:** both licenses chosen and written; CI is green on an empty workspace; scope doc drafted.

---

## M1 — qa-core domain, library-only (v0.1.0)

- [ ] **1.1 Core value objects (Parse-Don't-Validate)**
  - [ ] 1.1.1 `QuestionId`/`AnswerId`/`UserId` newtypes
  - [ ] 1.1.2 `Body` (non-empty, parsed) — empty body unrepresentable
  - [ ] 1.1.3 `Tag` with `date` and `jurisdiction` facets
  - [ ] 1.1.4 `License` enum (`CcBySa4`,`CcBy4`,`Native`,`LinkOnly`); unknown ⇒ parse error
- [ ] **1.2 `VerifiedCredential` value object**
  - [ ] 1.2.1 Opaque token; constructor private to verification crate (compile-fail test via trybuild)
  - [ ] 1.2.2 `scope` (Clinical/Engineering/Research) + `expiry`
  - [ ] 1.2.3 `authority_weight()` as pure fn of (scope, freshness)
- [ ] **1.3 Aggregates**
  - [ ] 1.3.1 `Question` with revision history
  - [ ] 1.3.2 `Answer` with revision history + optional credential weight
  - [ ] 1.3.3 `Vote` incl. `StillValid` variant (perishability signal)
- [ ] **1.4 Ports (traits) defined in qa-core**
  - [ ] 1.4.1 `CredentialPort`
  - [ ] 1.4.2 `ContentSourcePort`
  - [ ] 1.4.3 `SearchIndexPort`
  - [ ] 1.4.4 `PersistencePort`
- [ ] **1.5 Invariant tests**
  - [ ] 1.5.1 unknown-license-fails-to-parse
  - [ ] 1.5.2 core-cannot-forge-credential (trybuild compile-fail)
  - [ ] 1.5.3 architecture test: no outward deps from qa-core

**M1 exit:** `qa-core` compiles as a library with zero outward deps; invariants CI-enforced. No binary, no DB.

---

## M2 — Persistence + identity-verification (v0.2.0)

- [ ] **2.1 PersistencePort adapters**
  - [ ] 2.1.1 SQLite adapter (constrained single-binary path)
  - [ ] 2.1.2 Postgres adapter (hosted path)
  - [ ] 2.1.3 Shared conformance test-suite run against both
- [ ] **2.2 identity-verification crate**
  - [ ] 2.2.1 Generic adapter (ORCID + institutional email + manual review)
  - [ ] 2.2.2 Indonesia adapter (STR/KKI) — design + stub behind feature flag
  - [ ] 2.2.3 US adapter (NPI) — design + stub behind feature flag
  - [ ] 2.2.4 Credential expiry/lifecycle as typestate
- [ ] **2.3 Wire `CredentialPort` impl into qa-core via DI**

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

- [ ] 4.1 `SearchIndexPort` impl (tag-facet + full-text; SQLite FTS / Postgres tsvector or Tantivy)
- [ ] 4.2 Read-side projection (no writes to qa-core)
- [ ] 4.3 Faceted query: tag × jurisdiction × date (surfaces staleness)

## M5 — web client, minimal (v0.5.0)

- [ ] 5.1 TS/pnpm client: ask, answer, vote, search
- [ ] 5.2 Zod/Valibot at every API edge; branded types for ids
- [ ] 5.3 Credential badge rendering with safety copy (badge ≠ medical advice)
- [ ] 5.4 Attribution rendering for mirrored content

## M6 — Works → Community (v1.0.0 candidate)

- [ ] 6.1 Self-host single-binary (SQLite) path verified end-to-end
- [ ] 6.2 Community guidelines (on-topic/scope from 0.4 finalized)
- [ ] 6.3 Moderation tooling (close/flag, patient-advice rejection)
- [ ] 6.4 **Only now**: open to community. Not before it demonstrably works.

---

## Cross-cutting (every milestone)

- [ ] Boy Scout Rule: leave touched modules cleaner than found
- [ ] Chesterton's Fence: deferred designs (decay/context-envelope) stay documented, not deleted
- [ ] SemVer discipline: `cargo-semver-checks` gate before each tagged release
- [ ] Least privilege: each adapter gets only the access it needs
