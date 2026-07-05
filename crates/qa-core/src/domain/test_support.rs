//! Shared test-only doubles for domain ports.
//!
//! Kept in one place so multiple test modules (`ports::tests`, `answer::tests`)
//! don't hand-maintain their own copies of the same mock, which can drift out
//! of sync with `CredentialPort`'s actual contract as it evolves.

use crate::domain::credential::AuthoritySnapshot;
use crate::domain::id::UserId;
use crate::domain::ports::CredentialPort;
use std::collections::HashSet;

/// A `CredentialPort` that returns a fixed snapshot for a fixed set of
/// verified users, and `None` for everyone else.
pub(crate) struct MockCredentialPort {
    verified_users: HashSet<u64>,
    snapshot: AuthoritySnapshot,
}

impl MockCredentialPort {
    pub(crate) fn new(verified_users: Vec<u64>, snapshot: AuthoritySnapshot) -> Self {
        MockCredentialPort {
            verified_users: verified_users.into_iter().collect(),
            snapshot,
        }
    }
}

impl CredentialPort for MockCredentialPort {
    fn verify_credential(&self, user_id: UserId) -> Option<AuthoritySnapshot> {
        self.verified_users
            .contains(&user_id.inner())
            .then_some(self.snapshot)
    }
}
