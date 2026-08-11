---
type: Log
title: openstack-glance-operator-kog — log
description: Curated chronological history of openstack-glance-operator-kog — notable changes and decisions, not a generated changelog.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, glance, log, history]
timestamp: 2026-08-11T00:00:00Z
---

# Log

Curated history; release notes live in GitHub Releases.

## 2026-08-11 — Documentation Standard adoption

The repo adopts the Krateo Documentation Standard (OKF): the invariant docs bundle
(`index`, `overview`, `usage`, `configuration`, `api`, `examples`, `release`, `log`,
`llms.txt`), a rewritten `README.md` with the standard six sections, and frontmatter
on the pre-existing `docs/quickstart.md`. The single example is reorganized under
`examples/composition/` with its own `README.md`, and a `lint.yaml` wires the shared
`lint-docs` check. Part of krateo-platformops/installer#52.

## 2026-08-05 — 0.1.0: first release

The blueprint ships whole: a KOG chart emitting three per-resource
`RestDefinition`s (`Image`, `ImageImport`, `ImageMember`) over a hand-crafted
OpenAPI 3.0 subset each, plus the stateless openstacksdk auth-bridge that injects a
fresh auto-refreshing `X-Auth-Token` in front of Glance. Two Glance realities shape
the design:

- **No update verb.** Glance image update is JSON-Patch only, which KOG cannot emit,
  so `Image` carries only create / get / delete — change an image by delete +
  recreate.
- **No binary upload.** `PUT /v2/images/{id}/file` is octet-stream, out of KOG's
  reach; an `Image` creates only `queued` metadata, and `ImageImport`
  (`web-download`) populates it from a URL to reach `active`.
