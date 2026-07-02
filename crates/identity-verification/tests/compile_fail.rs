//! Compile-fail test for the credential-forgery boundary (task 1.5.2).
//!
//! Unlike the qa-core fixture (which proves qa-core has *no dependency* on this
//! crate, so it cannot even name `VerifiedCredential`), this fixture links this
//! crate as a normal external dependency and tries to call the `pub(crate)`
//! `issue` constructor with the correct signature. It must fail to compile
//! because the constructor is private to this crate — directly exercising the
//! privacy guarantee. If `issue` were ever made `pub`, this test would break.

#[test]
fn cannot_call_private_issue_constructor() {
    let t = trybuild::TestCases::new();
    t.compile_fail("tests/ui/cannot_call_issue.rs");
}

/// Compile-fail test for the read-typestate boundary (task 2.2.4).
///
/// Proves generic code cannot read credential fields (scope, user_id, etc.)
/// without the concrete `Active` state — see `tests/ui/cannot_read_non_active_state.rs`
/// for why this doesn't need to construct an Issued/Expired value directly.
#[test]
fn cannot_read_credential_without_active_state() {
    let t = trybuild::TestCases::new();
    t.compile_fail("tests/ui/cannot_read_non_active_state.rs");
}
