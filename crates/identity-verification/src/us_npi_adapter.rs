//! US jurisdiction adapter (NPI) — design stub, no external calls.
//!
//! See `docs/JURISDICTION-ADAPTER-US-NPI.md` for the full design rationale.
//!
//! This adapter's shape exists so the NPPES NPI registry integration has a
//! place to land, but the integration itself is deferred (task 2.2.3 scope:
//! design + stub only). `verify_credential` is a pure function that always
//! returns `None` — there is no network client and no registry lookup here
//! yet.
//!
//! Activation is gated by [`UsNpiAdapterConfig::enabled`], a runtime flag
//! rather than a Cargo feature: the module always compiles and its tests
//! always run in CI, but no deployment can start verifying US NPI
//! credentials before the real NPPES integration exists to back the flag.

use qa_core::domain::credential::AuthoritySnapshot;
use qa_core::domain::id::UserId;
use qa_core::domain::ports::CredentialPort;

/// A US NPI (National Provider Identifier) registration record.
///
/// Carries the fields a future NPPES registry lookup would need to
/// confirm. Not yet consumed by any verification logic — `UsNpiAdapter`
/// has no registry to check this against.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NpiRegistration {
    /// The 10-digit NPI number as issued by NPPES. Not validated against
    /// the Luhn check-digit — format validation is deferred to the real
    /// adapter.
    pub npi_number: String,
    /// Registered provider's name, for audit/manual cross-check only.
    pub provider_name: String,
}

/// Configuration for the US jurisdiction adapter (NPI).
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct UsNpiAdapterConfig {
    /// Feature flag controlling activation. Defaults to `false`. Even when
    /// `true`, `verify_credential` still returns `None` unconditionally —
    /// this flag is the wiring point the real NPPES integration will read,
    /// not a switch on any verification logic that exists today.
    pub enabled: bool,
}

/// US jurisdiction adapter (NPI) — stub implementation.
///
/// Implements `CredentialPort` so it can be wired into qa-core once the
/// real NPPES registry integration lands, but currently never issues a
/// credential regardless of configuration or registered NPI data.
#[derive(Clone, Debug, Default)]
pub struct UsNpiAdapter {
    config: UsNpiAdapterConfig,
}

impl UsNpiAdapter {
    /// Create a new US NPI adapter with the given configuration.
    pub fn new(config: UsNpiAdapterConfig) -> Self {
        UsNpiAdapter { config }
    }

    /// Whether this adapter is enabled by feature flag.
    ///
    /// Exposed for tests and diagnostics; does not affect verification
    /// outcome today since no verification logic exists yet.
    pub fn is_enabled(&self) -> bool {
        self.config.enabled
    }
}

impl CredentialPort for UsNpiAdapter {
    /// Always returns `None`.
    ///
    /// No NPPES NPI registry integration exists yet (see module docs and
    /// `docs/JURISDICTION-ADAPTER-US-NPI.md`). This makes no external
    /// calls, regardless of `self.config.enabled`.
    fn verify_credential(&self, _user_id: UserId) -> Option<AuthoritySnapshot> {
        None
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn disabled_adapter_never_verifies() {
        let adapter = UsNpiAdapter::new(UsNpiAdapterConfig { enabled: false });
        assert!(!adapter.is_enabled());
        assert_eq!(adapter.verify_credential(UserId::new(1)), None);
    }

    #[test]
    fn enabled_adapter_still_never_verifies() {
        // Pins down that flipping the flag today is a no-op, not an
        // accidental activation of unfinished verification logic.
        let adapter = UsNpiAdapter::new(UsNpiAdapterConfig { enabled: true });
        assert!(adapter.is_enabled());
        assert_eq!(adapter.verify_credential(UserId::new(1)), None);
    }

    #[test]
    fn default_config_is_disabled() {
        let config = UsNpiAdapterConfig::default();
        assert!(!config.enabled);
    }

    #[test]
    fn npi_registration_carries_expected_fields() {
        let reg = NpiRegistration {
            npi_number: "1234567893".to_string(),
            provider_name: "Dr. Test".to_string(),
        };
        assert_eq!(reg.npi_number, "1234567893");
        assert_eq!(reg.provider_name, "Dr. Test");
    }
}
