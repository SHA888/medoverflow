//! Integration test for task 2.3: wiring a `CredentialPort` implementation
//! into qa-core via dependency injection.
//!
//! This lives here (not in qa-core) precisely because it needs a *concrete*
//! adapter: identity-verification depends on qa-core, never the reverse, so
//! this is the natural composition point that owns both the port consumer
//! (`Answer::author_with_port`) and a real port implementation
//! (`GenericAdapter`). qa-core's `Cargo.toml` gains no new dependency.

use identity_verification::generic_adapter::GenericAdapter;
use identity_verification::CredentialScope;
use qa_core::domain::answer::Answer;
use qa_core::domain::body::Body;
use qa_core::domain::id::{AnswerId, UserId};
use qa_core::domain::license::License;
use std::time::{Duration, SystemTime};

#[test]
fn answer_authored_via_injected_generic_adapter_carries_real_authority_weight() {
    let mut adapter = GenericAdapter::new(Duration::from_secs(365 * 24 * 3600))
        .with_orcid(CredentialScope::Engineering);
    adapter.register_orcid("7".to_string(), "0000-0001-2345-6789".to_string());

    // qa-core receives the concrete adapter only as `&dyn CredentialPort` —
    // this is the dependency-injection seam itself.
    let answer = Answer::author_with_port(
        &adapter,
        AnswerId::new(1),
        Body::new("Answers via the wired credential port").unwrap(),
        UserId::new(7),
        SystemTime::now(),
        License::Native,
    );

    let snapshot = answer.credential().expect("verified author has authority");
    assert_eq!(
        snapshot.scope(),
        qa_core::domain::credential::CredentialScope::Engineering
    );
    // A freshly-issued, freshly-activated credential is at full freshness:
    // weight equals the scope's base weight (Engineering = 1.0).
    assert_eq!(snapshot.weight().value(), 1.0);
}

#[test]
fn answer_authored_via_injected_adapter_has_no_authority_for_unverified_user() {
    let adapter = GenericAdapter::new(Duration::from_secs(365 * 24 * 3600));

    let answer = Answer::author_with_port(
        &adapter,
        AnswerId::new(2),
        Body::new("Answer from an unverified author").unwrap(),
        UserId::new(999),
        SystemTime::now(),
        License::Native,
    );

    assert!(!answer.has_credential());
}
