---
type: API
title: openstack-glance-operator-kog — API
description: The CompositionDefinition CRD this blueprint registers and the generated Glance resource CRDs (Image, ImageImport, ImageMember), including the RestDefinition verbs each is built from.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, compositiondefinition, restdefinition, glance]
timestamp: 2026-08-11T00:00:00Z
---

# API

This blueprint exposes two layers of API: the `CompositionDefinition` that
registers the chart with Krateo, and the per-resource CRDs `oasgen-provider`
generates from the chart's `RestDefinition`s.

## The CompositionDefinition CRD

`compositiondefinition.yaml` is a `CompositionDefinition`
(`core.krateo.io/v1alpha1`) — the resource Krateo's core-provider watches to install
a blueprint. This repo ships its own:

```yaml
apiVersion: core.krateo.io/v1alpha1
kind: CompositionDefinition
metadata:
  name: openstack-glance-operator-kog
  namespace: krateo-system
spec:
  chart:
    url: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
    version: "0.1.0"
```

| field | meaning |
|---|---|
| `spec.chart.url` | The OCI location of the published chart. `release-chart.yaml` pushes to `oci://ghcr.io/<owner>/charts/<name>`. |
| `spec.chart.version` | The chart version to install; must match a published tag / `Chart.yaml` version. |

From this CD, core-provider derives a generated composition API. The **Kind** is the
PascalCase of `metadata.name` with hyphens dropped
(`openstack-glance-operator-kog` → `OpenstackGlanceOperatorKog`) and the
**apiVersion** comes from the chart version (`0.1.0` → `composition.krateo.io/v0-1-0`).
Applying an instance of that Kind installs the operator layer; its `spec` mirrors the
chart values ([configuration](./configuration.md), [examples](./examples.md)).

## The RestDefinition (`ogen.krateo.io/v1alpha1`)

For each enabled resource the chart emits a `RestDefinition` (`rd-*.yaml`) that points
`oasgen-provider` at a ConfigMap carrying the OpenAPI subset (`assets/*.yaml`) and
declares the verbs. `oasgen-provider` reads it and generates the resource CRD plus a
`rest-dynamic-controller`. Their `resourceGroup`/`resourceKind` are configurable
([configuration](./configuration.md)).

## Generated Glance resource CRDs

The controller reconciles instances of these Kinds against Glance v2. Each CR also
references a `<Kind>Configuration` naming the bearer token secret (the auth-bridge
injects the real token).

### `Image` — `image.openstack.krateo.io/v1alpha1`

Image metadata: create / get / delete. **No update verb** (Glance image update is
JSON-Patch only). Identifiers: `id`, `name`. Status fields: `id`, `status`.

| verb | method / path |
|---|---|
| create | `POST /v2/images` |
| get | `GET /v2/images/{id}` (from `status.id`) |
| delete | `DELETE /v2/images/{id}` (from `status.id`) |

Key spec fields: `name` (required), `disk_format` (required, e.g. `qcow2`, `raw`,
`iso`), `container_format` (required, e.g. `bare`, `ovf`), `visibility`
(`public`/`private`/`shared`/`community`), `min_disk`, `min_ram`, `protected`,
`tags`. Read-only status: `id`, `status`, `size`, `checksum`. A freshly created
image is `queued` until data is supplied via `ImageImport`.

### `ImageImport` — `image.openstack.krateo.io/v1alpha1`

A single-fire action: trigger a web-download import on a queued image so Glance
fetches the data from a URL and the image becomes `active`. Identifier: `image_id`.

| verb | method / path |
|---|---|
| findby | `GET /v2/images` (`OR` match — never matches `image_id`, so create always fires) |
| create | `POST /v2/images/{image_id}/import` (`image_id` from `spec.image_id`) |

Spec: `image_id` (required — the queued image), `method.name` (use `web-download`),
`method.uri` (source URL of the image data). Prerequisite: the image must be `queued`
and the Glance deployment must enable the `web-download` import method.

### `ImageMember` — `image.openstack.krateo.io/v1alpha1`

Share an image with another project: create / get / delete a member. Identifier:
`member`. Status fields: `member_id`, `status`.

| verb | method / path |
|---|---|
| create | `POST /v2/images/{image_id}/members` (`image_id` from `spec.image_id`) |
| get | `GET /v2/images/{image_id}/members/{member_id}` |
| delete | `DELETE /v2/images/{image_id}/members/{member_id}` |

Spec: `image_id` (required — the image to share), `member` (required — the target
project id). A member's `status` (accept / reject) is set by the target project and
is read-only here.
