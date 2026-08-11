---
type: Runbook
title: openstack-glance-operator-kog — release
description: How a release ships — a SemVer tag publishes the chart to GHCR via release-chart.yaml, and the CompositionDefinition is bumped to the published version.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, glance, release, oci]
timestamp: 2026-08-11T00:00:00Z
---

# Release

A plain-SemVer tag (`X.Y.Z`, **no** `v` prefix) publishes the chart. The push to a
matching tag triggers `.github/workflows/release-chart.yaml`.

## What a tag ships

`release-chart.yaml`:

1. `helm lint chart` — validates the chart and its `values.schema.json`.
2. Verifies the git tag equals `chart/Chart.yaml`'s `version` (a mismatch fails the
   run).
3. `helm package chart` and pushes the `.tgz` to
   `oci://ghcr.io/<owner>/charts` (the owner namespace is derived from the
   repository, so `GITHUB_TOKEN` only writes its own namespace) — with a small retry
   loop for GHCR first-push flakiness.

The published artifact is
`oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog`, which is what
`compositiondefinition.yaml`'s `spec.chart.url` points at.

## Steps

```console
$ git tag X.Y.Z && git push origin X.Y.Z
```

The chart version, `appVersion`, and the tag must all be `X.Y.Z`. After the chart is
published, bump `compositiondefinition.yaml`'s `spec.chart.version` to `X.Y.Z` on
`main` so this component's own registration points at a version that exists.

Verify the artifact:

```console
$ helm show chart oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog --version X.Y.Z | head -3
```

## PR-time checks

`security.yml` runs the shared security workflow on every PR and push to `main`.
`lint.yaml` runs the shared docs-standard linter (`lint-docs`), which enforces the
Krateo Documentation Standard across `docs/**` and `examples/**`.
