//! Tests for Body value object (task 1.1.2).
//!
//! Body makes empty and whitespace-only payloads unrepresentable at the type level.
//! Parsing enforces the invariant: illegal strings fail at construction, not at usage.

#[test]
fn empty_string_fails() {
    use qa_core::domain::body::Body;

    let result = Body::new("");
    assert!(result.is_err());
}

#[test]
fn whitespace_only_fails() {
    use qa_core::domain::body::Body;

    assert!(Body::new("   ").is_err());
    assert!(Body::new("\n").is_err());
    assert!(Body::new("\t").is_err());
    assert!(Body::new("  \n\t  ").is_err());
}

#[test]
fn valid_string_succeeds() {
    use qa_core::domain::body::Body;

    let body = Body::new("Hello, world!").expect("valid string");
    assert_eq!(body.as_str(), "Hello, world!");
}

#[test]
fn string_with_leading_trailing_space_succeeds() {
    use qa_core::domain::body::Body;

    let body = Body::new("  leading and trailing  ").expect("valid string");
    assert_eq!(body.as_str(), "  leading and trailing  ");
}

#[test]
fn body_clone() {
    use qa_core::domain::body::Body;

    let body1 = Body::new("test").expect("valid");
    let body2 = body1.clone();
    assert_eq!(body1.as_str(), body2.as_str());
}

#[test]
fn body_display() {
    use qa_core::domain::body::Body;

    let body = Body::new("Test content").expect("valid");
    assert_eq!(format!("{}", body), "Test content");
}

#[test]
fn body_equality() {
    use qa_core::domain::body::Body;

    let body1 = Body::new("test").expect("valid");
    let body2 = Body::new("test").expect("valid");
    let body3 = Body::new("other").expect("valid");

    assert_eq!(body1, body2);
    assert_ne!(body1, body3);
}

#[test]
fn body_error_types() {
    use qa_core::domain::body::{Body, BodyError};

    let empty_err = Body::new("").unwrap_err();
    match empty_err {
        BodyError::Empty => {} // expected
        _ => panic!("expected Empty error"),
    }

    let whitespace_err = Body::new("   ").unwrap_err();
    match whitespace_err {
        BodyError::WhitespaceOnly => {} // expected
        _ => panic!("expected WhitespaceOnly error"),
    }
}
