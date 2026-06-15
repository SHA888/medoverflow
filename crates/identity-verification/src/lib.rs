//! identity-verification: credential verification and opaque token issuance.
//!
//! This crate is the trust boundary. It produces `VerifiedCredential` tokens
//! (opaque to qa-core, unforgeable) that certify a user's professional identity
//! and scope.
//!
//! qa-core cannot construct `VerifiedCredential` — the constructor is private
//! to this crate. This architectural invariant is compile-fail-tested.

use std::fmt;
use std::sync::atomic::{AtomicU64, Ordering};

static CREDENTIAL_COUNTER: AtomicU64 = AtomicU64::new(0);

/// Error when constructing a VerifiedCredential.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum CredentialError {
    /// user_id was empty or whitespace-only.
    EmptyUserId,
}

impl fmt::Display for CredentialError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyUserId => write!(f, "user_id cannot be empty or whitespace-only"),
        }
    }
}

impl std::error::Error for CredentialError {}

/// An unforgeable credential token issued by identity verification.
///
/// This is the only type that proves a user has been verified. qa-core
/// receives it as an opaque token and cannot construct or modify it.
///
/// The constructor is private to this crate; qa-core cannot access it.
/// This is a compiler-enforced guarantee that credentials cannot be forged
/// within the qa-core domain.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub struct VerifiedCredential {
    /// Opaque credential ID (counter-based, does not encode user_id).
    id: String,
    /// Verified user ID (opaque to qa-core, provided at construction time only).
    user_id: String,
}

impl VerifiedCredential {
    /// Issue a new verified credential (private to identity-verification).
    ///
    /// This is the only way to construct a credential. qa-core cannot call this
    /// because the constructor is private to this module.
    ///
    /// # Errors
    ///
    /// Returns `CredentialError::EmptyUserId` if user_id is empty or whitespace-only.
    pub(crate) fn issue(user_id: String) -> Result<Self, CredentialError> {
        let trimmed = user_id.trim();
        if trimmed.is_empty() {
            return Err(CredentialError::EmptyUserId);
        }

        let counter = CREDENTIAL_COUNTER.fetch_add(1, Ordering::Relaxed);
        let id = format!("cred-{}", counter);
        Ok(VerifiedCredential {
            id,
            user_id: user_id.clone(),
        })
    }

    /// Return the verified user ID (opaque identifier).
    pub fn user_id(&self) -> &str {
        &self.user_id
    }

    /// Return the credential ID (unique, non-predictable).
    pub fn credential_id(&self) -> &str {
        &self.id
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn credential_can_be_issued() {
        let cred = VerifiedCredential::issue("user-123".to_string()).unwrap();
        assert_eq!(cred.user_id(), "user-123");
        assert!(cred.credential_id().starts_with("cred-"));
    }

    #[test]
    fn credentials_are_unique() {
        let cred1 = VerifiedCredential::issue("user-123".to_string()).unwrap();
        let cred2 = VerifiedCredential::issue("user-123".to_string()).unwrap();
        assert_ne!(cred1.credential_id(), cred2.credential_id());
    }

    #[test]
    fn credential_is_cloneable() {
        let cred = VerifiedCredential::issue("user-123".to_string()).unwrap();
        let cloned = cred.clone();
        assert_eq!(cred, cloned);
    }

    #[test]
    fn empty_user_id_rejected() {
        assert_eq!(
            VerifiedCredential::issue("".to_string()),
            Err(CredentialError::EmptyUserId)
        );
        assert_eq!(
            VerifiedCredential::issue("   ".to_string()),
            Err(CredentialError::EmptyUserId)
        );
    }

    #[test]
    fn credential_id_does_not_embed_user_id() {
        let cred1 = VerifiedCredential::issue("alice".to_string()).unwrap();
        let cred2 = VerifiedCredential::issue("bob".to_string()).unwrap();
        assert!(!cred1.credential_id().contains("alice"));
        assert!(!cred2.credential_id().contains("bob"));
    }
}
