# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Realtime queueing system with number issuing, configurable service
  counters, TV display, and admin control pages.
- PIN-protected access for staff pages; the TV display is public and
  read-only.
- Skip, requeue, delete, and reorder ticket actions from the admin screen.
- Recall-previous, so a counter can undo its last served or skipped ticket.
- Configurable number of counters, each with its own PIN, changeable
  without retyping unchanged PINs.
- Bulk-issue numbers from the admin screen, for pre-registered attendees
  or seeding the queue ahead of time.
- Optional beep or spoken announcement on the TV display when a number is
  called.
- Mobile-responsive layout across all four pages.
- WebSocket broadcast of queue state to all connected pages.
- JSON file persistence, no database required, with crash-safe atomic
  writes.
- CI pipeline running lint, format checks, and the test suite.
