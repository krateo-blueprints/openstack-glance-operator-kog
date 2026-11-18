---
type: Log
title: openstack-glance-operator-kog — log
description: Curated chronological history of openstack-glance-operator-kog — notable changes and decisions, not a generated changelog.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, glance, log, history]
timestamp: 2026-11-18T00:00:00Z
---

# Log

Curated history; release notes live in GitHub Releases.

## Unreleased — `ImageMember` fills `status.member`; status-field gate

`ImageMember`'s identifier `member` is not in Glance's member representation. Glance returns
`member_id`, `image_id`, `status`, `created_at`, `updated_at` and `schema`
(`glance/api/v2/image_members.py` `_format_image_member`), so `status.member` was always empty.
Create, observe and Ready were unaffected: the get is addressed from `spec.member`, and an absent key
is not drift. Response fieldMappings on create and get now copy `member_id` to `member`, and keep
`member_id`, which is also a status field. So `status.member` fills in, and `spec.member` is compared
against what Glance returns.

New CI gate `hack/validate-status-fields.py`, ported from neutron-kog. It now models a mapping's
source removal: a status field whose source a fieldMapping moves elsewhere is reported, because the
normalization removes it. main's `ImageMember` fails it, and so does a mapping that drops `member_id`.

## Unreleased — `ImageImport` is observed through the image and fires once

`ImageImport` used a findby on `GET /v2/images` keyed on `image_id`. Glance's image items carry
`id`, so it could never match, and the item schema was `additionalProperties: true`, so nothing
showed it. It worked only through the `202` latching a Pending condition. Per
rest-dynamic-controller 0.80.0's source, that condition reports exists without ever setting
Available, so the CR could not become Ready. And if the latch was lost, the re-import of an active
image was a permanent `409` (issue #14; same class as keystone-kog 0.4.2's role assignment).

It now reads `GET /v2/images/{image_id}`. A `notFoundBody` predicate fires the import only while the
image is `queued`, unlocked, and carries neither of the store-bookkeeping keys Glance writes when an
import flow starts (`os_glance_importing_to_stores`, `os_glance_failed_import`). A failed import
reverts the image to `queued` but keeps those keys, so it is not retried in a loop. Ready means the
import was accepted; `status.status` shows progress. Gated in CI by
`hack/test-image-import-predicate.py`, which covers 8 image states and self-tests that a
status-only predicate would re-fire the failed import, and by `hack/validate-findby-identifiers.py`.

Also: the Glance Kinds are served at `v2-0` (from the OAS `info.version`), not `v1alpha1`; the
docs and samples are corrected.

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
