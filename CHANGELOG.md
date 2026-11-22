# Changelog

All notable changes to the inboxili Python package are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses [Semantic Versioning](https://semver.org/).

## [0.1.1] - 2026-11-22

### Added
- `SendEmailResponse.queue_id`, and HTTP 202 `queued` responses are treated as success. Each API key now delivers at most 100 emails a minute and queues the rest.

## [0.1.0] - 2026-10-07

### Added
- Initial release: send a transactional email through `POST /api/v1/transactional/send`, typed errors, opt-in 429 retry, and webhook signature verification.
