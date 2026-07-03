//! Shared scaffold for jurisdiction adapter stubs (design-only, task 2.2.2/2.2.3).
//!
//! `IndonesiaAdapter` (STR/KKI) and `UsNpiAdapter` (NPI) are both instances of
//! this same shape: a runtime-flagged adapter that implements `CredentialPort`
//! but never issues a credential, because the jurisdiction-specific registry
//! integration is deferred. Factoring the shape out here means a future
//! jurisdiction stub (or a change to the stub contract itself — e.g. what the
//! runtime flag gates) has exactly one place to add or fix, not one per
//! jurisdiction.
//!
//! `Registration` is the jurisdiction-specific registration record type (e.g.
//! `StrRegistration`, `NpiRegistration`). It is carried only as a `PhantomData`
//! marker here — no verification logic reads it yet — so each jurisdiction
//! module still owns its own registration data shape and doc rationale; only
//! the stub adapter behavior itself is shared.

use qa_core::domain::credential::AuthoritySnapshot;
use qa_core::domain::id::UserId;
use qa_core::domain::ports::CredentialPort;
use std::fmt;
use std::marker::PhantomData;

/// Runtime activation flag shared by every jurisdiction adapter stub.
///
/// Defaults to `false`. Even when `true`, `verify_credential` still returns
/// `None` unconditionally — this flag is the wiring point a real registry
/// integration will read, not a switch on any verification logic that exists
/// today.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct StubAdapterConfig {
    pub enabled: bool,
}

/// A jurisdiction adapter stub: always compiles, always tests, never verifies.
///
/// Implements `CredentialPort` so it can be wired into qa-core once a real
/// jurisdiction registry integration lands, but currently never issues a
/// credential regardless of configuration or registered data.
pub struct StubJurisdictionAdapter<Registration> {
    config: StubAdapterConfig,
    _registration: PhantomData<Registration>,
}

// Implemented by hand (rather than `#[derive(..)]`) so these impls do not
// require `Registration: Clone + Debug + Default` — the field is a marker,
// never an actual `Registration` value, so no such bound should leak out.
impl<Registration> Clone for StubJurisdictionAdapter<Registration> {
    fn clone(&self) -> Self {
        StubJurisdictionAdapter {
            config: self.config,
            _registration: PhantomData,
        }
    }
}

impl<Registration> fmt::Debug for StubJurisdictionAdapter<Registration> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("StubJurisdictionAdapter")
            .field("config", &self.config)
            .finish()
    }
}

impl<Registration> Default for StubJurisdictionAdapter<Registration> {
    fn default() -> Self {
        StubJurisdictionAdapter {
            config: StubAdapterConfig::default(),
            _registration: PhantomData,
        }
    }
}

impl<Registration> StubJurisdictionAdapter<Registration> {
    /// Create a new jurisdiction adapter stub with the given configuration.
    pub fn new(config: StubAdapterConfig) -> Self {
        StubJurisdictionAdapter {
            config,
            _registration: PhantomData,
        }
    }

    /// Whether this adapter is enabled by feature flag.
    ///
    /// Exposed for tests and diagnostics; does not affect verification
    /// outcome today since no verification logic exists yet.
    pub fn is_enabled(&self) -> bool {
        self.config.enabled
    }
}

impl<Registration> CredentialPort for StubJurisdictionAdapter<Registration> {
    /// Always returns `None`.
    ///
    /// No jurisdiction registry integration exists yet for any stub adapter.
    /// This makes no external calls, regardless of `self.config.enabled`.
    fn verify_credential(&self, _user_id: UserId) -> Option<AuthoritySnapshot> {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Stands in for a jurisdiction-specific registration record. Stub
    /// behavior does not depend on which `Registration` type is used, so
    /// testing it once here (rather than per jurisdiction module) covers
    /// every `StubJurisdictionAdapter<R>` instantiation.
    #[derive(Debug)]
    struct TestRegistration;

    #[test]
    fn disabled_adapter_never_verifies() {
        let adapter =
            StubJurisdictionAdapter::<TestRegistration>::new(StubAdapterConfig { enabled: false });
        assert!(!adapter.is_enabled());
        assert_eq!(adapter.verify_credential(UserId::new(1)), None);
    }

    #[test]
    fn enabled_adapter_still_never_verifies() {
        // Pins down that flipping the flag today is a no-op, not an
        // accidental activation of unfinished verification logic.
        let adapter =
            StubJurisdictionAdapter::<TestRegistration>::new(StubAdapterConfig { enabled: true });
        assert!(adapter.is_enabled());
        assert_eq!(adapter.verify_credential(UserId::new(1)), None);
    }

    #[test]
    fn default_config_is_disabled() {
        let config = StubAdapterConfig::default();
        assert!(!config.enabled);
    }
}
