---
type: Component
title: openstack-glance-operator-kog — index
description: The map of the openstack-glance-operator-kog doc bundle — a Krateo Operator Generator blueprint that turns OpenStack Glance (image v2) resources into native Kubernetes custom resources.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, oasgen-provider, openstack, glance]
timestamp: 2026-08-11T00:00:00Z
---

# openstack-glance-operator-kog

A Krateo Operator Generator (KOG) blueprint: a Helm chart plus a sibling
`CompositionDefinition` that turns **OpenStack Glance (image v2)** resources into
native Kubernetes custom resources — no hand-written controller, just a curated
OpenAPI subset per resource driven by `oasgen-provider` and the generic
`rest-dynamic-controller`.

The chart emits three per-resource `RestDefinition`s (`Image`, `ImageImport`,
`ImageMember`) and a stateless Keystone-auth **auth-bridge** proxy that injects a
fresh, auto-refreshing `X-Auth-Token` in front of Glance.

## The bundle (start here)

- [overview](./overview.md) — what the blueprint does, the KOG pipeline, the two
  Glance realities (no update verb, no binary upload) and the auth-bridge design.
- [usage](./usage.md) — install the operator, create an `Image`, populate it with an
  `ImageImport`, share it with an `ImageMember`.
- [configuration](./configuration.md) — the whole `values.yaml` surface: per-resource
  toggles and the auth-bridge knobs.
- [api](./api.md) — the `CompositionDefinition` CRD this repo registers and the
  generated Glance resource CRDs (`Image`, `ImageImport`, `ImageMember`).
- [examples](./examples.md) — the runnable example under `examples/`.
- [release](./release.md) — how a tag ships the chart to GHCR.
- [log](./log.md) — curated history.
- [llms.txt](./llms.txt) — the doc index for LLMs.
- [quickstart](./quickstart.md) — the short end-to-end path to an active image in
  Horizon.

## Layout

- `chart/` — the blueprint chart.
  - `assets/` — the hand-crafted OpenAPI 3.0 subsets (`image.yaml`,
    `image-import.yaml`, `image-member.yaml`), one per resource.
  - `templates/` — the `RestDefinition`s (`rd-*.yaml`), their backing ConfigMaps
    (`configmap-*.yaml`), and the auth-bridge Deployment/Service/ConfigMap.
  - `scripts/openstack-auth-proxy.py` — the openstacksdk Keystone-auth proxy.
  - `samples/image-resources.yaml` — sample Glance CRs to apply once the operator
    is up.
  - `values.yaml` + `values.schema.json` — the value surface, fully typed.
- `compositiondefinition.yaml` — this blueprint's own registration
  (`core.krateo.io/v1alpha1`), pointing at the published chart.
- `examples/composition.yaml` — an example `CompositionDefinition`-driven install.
