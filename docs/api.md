---
type: API
title: openstack-glance-operator-kog — API
description: The CompositionDefinition CRD this blueprint registers and the generated Glance resource CRDs (Image, ImageImport, ImageMember), including the RestDefinition verbs each is built from.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, compositiondefinition, restdefinition, glance]
timestamp: 2026-11-18T00:00:00Z
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

The controller reconciles instances of these Kinds against Glance v2. They are served at
version **`v2-0`**, which oasgen-provider derives from each OAS document's `info.version`
(`"2.0"`). Each CR also references a `<Kind>Configuration`, always `v1alpha1`, naming the
bearer token secret (the auth-bridge injects the real token). Until this release the docs
and samples said `v1alpha1` for the Glance Kinds, which the apiserver rejects with "no
matches for kind".

### `Image` — `image.openstack.krateo.io/v2-0`

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

### `ImageImport` — `image.openstack.krateo.io/v2-0`

Trigger a web-download import on a queued image so Glance fetches the data from a URL
and the image becomes `active`. Identifier: `image_id`. Status: `image_id`, `status`
(the image's: `queued` → `importing` → `active`), `os_glance_import_task`,
`os_glance_failed_import`.

| verb | method / path |
|---|---|
| get | `GET /v2/images/{image_id}`, with a `notFoundBody` predicate (below) |
| create | `POST /v2/images/{image_id}/import` (`image_id` from `spec.image_id`) → `202` |

The import fires only while the image shows **no sign that an import ever started**:
`status` is `queued`, there is no import lock (`os_glance_import_task`), and neither
`os_glance_importing_to_stores` nor `os_glance_failed_import` is present. Glance writes
those two keys when the import flow starts and never removes them on the web-download
path. A failed import therefore stays failed instead of being retried every reconcile:
the image reverts to `queued`, but the keys remain. To retry, create a new image.

**Ready means the import was accepted, not that the image is active.** Read
`status.status` for progress. A Ready `ImageImport` whose `status.status` is still
`queued` with no `os_glance_import_task` means the import ran and failed. Check the task
with `GET /v2/images/{image_id}/tasks`; Glance keeps it for `task_time_to_live`, 48 h by
default.

Until 0.1.x this kind used a `findby` on `GET /v2/images` keyed on `image_id`. Glance's
image items carry `id`, so it could never match, and it relied on the `202` latching a
Pending condition, under which the CR could not become Ready.

Spec: `image_id` (required — the queued image), `method.name` (use `web-download`),
`method.uri` (source URL of the image data). Prerequisite: the image must be `queued`
and the Glance deployment must enable the `web-download` import method.

### `ImageMember` — `image.openstack.krateo.io/v2-0`

Share an image with another project: create / get / delete a member. Identifier:
`member`. Status fields: `member` and `member_id` (both the member project id), `status`.
Glance's member representation has `member_id`, not `member`
(`glance/api/v2/image_members.py` `_format_image_member`), so response fieldMappings copy it
to `member`. Through 0.1.2 `status.member` stayed empty. Observation and readiness were never
affected, because the get is addressed from `spec.member`.

| verb | method / path |
|---|---|
| create | `POST /v2/images/{image_id}/members` (`image_id` from `spec.image_id`) |
| get | `GET /v2/images/{image_id}/members/{member_id}` |
| delete | `DELETE /v2/images/{image_id}/members/{member_id}` |

Spec: `image_id` (required — the image to share), `member` (required — the target
project id). A member's `status` (accept / reject) is set by the target project and
is read-only here.
