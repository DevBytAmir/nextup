# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Realtime queueing system with number issuing, two counters, TV display,
  and admin control pages.
- PIN-protected access for staff pages; the TV display is public and
  read-only.
- Skip, requeue, delete, and reorder ticket actions from the admin screen.
- WebSocket broadcast of queue state to all connected pages.
- JSON file persistence, no database required.
- CI pipeline running lint, format checks, and the test suite.
