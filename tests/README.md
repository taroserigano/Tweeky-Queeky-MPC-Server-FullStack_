# Test Suite

Comprehensive test coverage for Tweeky-Queeky Shop e-commerce platform.

## Test Structure

```
tests/
├── e2e/               # End-to-end workflow tests
├── api/               # API endpoint tests
├── integration/       # Integration tests
├── config/            # Configuration & connection tests
└── features/          # Feature-specific tests
    ├── auth/          # Authentication tests
    ├── payments/      # Payment processing tests
    ├── products/      # Product management tests
    └── reviews/       # Review functionality tests
```

## Running Tests

### Run all tests

```bash
python -m pytest tests/
```

### Run specific category

```bash
python -m pytest tests/e2e/
python -m pytest tests/api/
python -m pytest tests/features/reviews/
```

### Run individual test

```bash
python -m tests.config.test_atlas_connection
python -m tests.features.reviews.test_review_append
```

## Test Categories

### E2E Tests (5 tests)

Complete end-to-end user workflows testing the entire application stack.

### API Tests (5 tests)

Direct API endpoint testing for all major routes.

### Integration Tests (3 tests)

Testing integration between different components and services.

### Config Tests (5 tests)

Database connections, port configurations, and environment setup.

### Feature Tests (12 tests)

- **Auth** (1 test): JWT cookie authentication
- **Payments** (1 test): Payment processing stress tests
- **Products** (1 test): Product creation and management
- **Reviews** (5 tests): Review append, multi-user reviews, comprehensive testing
