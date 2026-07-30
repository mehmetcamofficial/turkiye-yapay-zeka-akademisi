# Test Strategy

Run focused unit tests first, then project integration tests, canonical offline
evaluation, isolated tracked-checkout tests, and proportional workspace checks.
Asset-required research tests must declare their dependency. Browser scripts
must not be interpreted as ordinary pytest tests without fixtures.

Current tracked suites include Copilot, portfolio integrity, search evaluation,
quality-gate mutation, suggested-query, and Trendyol version tests.

