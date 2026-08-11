---
type: ExampleIndex
title: openstack-glance-operator-kog — examples
description: Index of the runnable examples under examples/.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, glance, examples]
timestamp: 2026-08-11T00:00:00Z
---

# Examples

- [examples/composition](../examples/composition/README.md) — install the Glance KOG
  operator layer (the per-resource `RestDefinition`s plus the auth-bridge) through a
  Krateo `CompositionDefinition`-derived `OpenstackGlanceOperatorKog` CR, configured
  entirely through the composition spec.

For the raw `helm install` path and the day-2 CRs (`Image`, `ImageImport`,
`ImageMember`), see [usage](./usage.md) and the ready-to-edit
`chart/samples/image-resources.yaml`.
