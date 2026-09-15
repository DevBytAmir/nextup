# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0]

### Added

- Realtime queueing system with number issuing, configurable service
  counters, TV display, and admin control pages.
- PIN-protected access for staff pages, each counter authenticated with
  its own PIN; the TV display is public and read-only.
- Skip, requeue, delete, and reorder ticket actions from the admin screen.
- Recall-previous, so a counter can undo its last served or skipped
  ticket, based on actual recency rather than ticket number.
- Configurable number of counters, each with its own PIN, changeable
  without retyping unchanged PINs. Removing or reassigning a counter
  revokes its existing session and clears stale ticket references.
- Bulk-issue numbers from the admin screen, for pre-registered attendees
  or seeding the queue ahead of time.
- Optional beep or spoken announcement on the TV display when a number is
  called.
- Mobile-responsive layout across all four pages, all with live updates
  over WebSocket.
- JSON file persistence, no database required, with crash-safe atomic
  writes and automatic recovery from a corrupt state file.
- PIN checks use constant-time comparison; a real logout revokes a
  session server-side on every page.
- CI pipeline running lint, format checks, and the test suite.

[Unreleased]: https://github.com/DevBytAmir/nextup/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/DevBytAmir/nextup/releases/tag/v1.0.0
