---
type: Architecture
title: openstack-glance-operator-kog — overview
description: What the blueprint does and how it is built — the KOG pipeline, the three per-resource RestDefinitions, the two Glance realities (no update verb, no binary upload), and the auto-refreshing auth-bridge.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, glance, restdefinition, auth-bridge]
timestamp: 2026-08-11T00:00:00Z
---

# Overview

openstack-glance-operator-kog is a Krateo Operator Generator (KOG) blueprint. It
turns **OpenStack Glance image v2** resources into native Kubernetes custom
resources without a hand-written controller: each resource is described by a curated
OpenAPI 3.0 subset (`chart/assets/*.yaml`), the chart hands it to `oasgen-provider`
via a `RestDefinition`, and the generic `rest-dynamic-controller` reconciles the
resulting CRs against the Glance API.

## The KOG pipeline

One `helm install` renders, per enabled resource, two manifests
(`chart/templates/`):

| manifest | kind | role |
|---|---|---|
| `configmap-<resource>.yaml` | `ConfigMap` | carries the OpenAPI subset from `chart/assets/<resource>.yaml` |
| `rd-<resource>.yaml` | `RestDefinition` (`ogen.krateo.io/v1alpha1`) | points `oasgen-provider` at that ConfigMap and declares the verbs |

`oasgen-provider` reads the `RestDefinition`, generates the CRD and a matching
`rest-dynamic-controller` deployment, and that controller then reconciles instances
of the generated Kind by calling the Glance REST endpoints named in
`spec.resource.verbsDescription`.

Glance v2 uses **flat JSON** (no envelope), so there is no crdgen
Kind-vs-property collision and the Kinds are unprefixed (`Image`, `ImageImport`,
`ImageMember`).

## The three resources

| Kind | Glance API | verbs | notes |
|---|---|---|---|
| `Image` | `/v2/images` | create (metadata) / get / delete | no update verb — see below |
| `ImageImport` | `POST /v2/images/{id}/import` | web-download import (single-fire) | `findby` never matches, so create fires exactly once |
| `ImageMember` | `/v2/images/{id}/members` | share (create) / get / unshare (delete) | disabled by default in the example |

Each resource can be toggled independently under
`restdefinitions.<name>.enabled` ([configuration](./configuration.md)).

## Two Glance realities to know

**No `update` verb.** A Glance image update is **JSON-Patch only**
(`application/openstack-images-v2.1-json-patch`), a content type KOG cannot emit. So
the `Image` `RestDefinition` carries only create / get / delete — change an image by
delete + recreate (the same constraint the Ironic operator's `Node` lives with).

**Binary upload is out of KOG's reach.** `PUT /v2/images/{id}/file` is an
octet-stream upload, not JSON. So an `Image` creates only the **metadata** (the
image lands in status `queued`). To get a usable (`active`) image, apply an
**`ImageImport`** with `method.name: web-download` and a source `uri` — Glance
fetches the data itself. This requires the `web-download` import method to be
enabled on the Glance deployment. The `ImageImport` is modeled as a single-fire
action (like KOG's `NodeProvision`): its `findby` verb never matches `image_id`, so
`create` (`POST .../import`) fires once and the `202` sets a Pending condition.

## Auth: the openstacksdk proxy (auto-refreshing)

The generated controller makes plain-HTTP calls, but Glance requires a Keystone
`X-Auth-Token` that expires. The chart ships an **auth-bridge**
(`chart/scripts/openstack-auth-proxy.py`, run with `SERVICE_TYPE=image`): a stateless
reverse proxy that authenticates with your `clouds.yaml`, discovers the `image`
endpoint from the Keystone catalog, and injects a fresh, auto-refreshing
`X-Auth-Token` before forwarding upstream. It is in-cluster-safe and is the same
auth-bridge the sibling OpenStack KOG operators use.

The OpenAPI subsets point their `servers[0].url` at the in-cluster auth-bridge
Service (`_helpers.tpl` `authBridgeUrl`), so the controller talks to the proxy and
the proxy talks to Glance. Set `authBridge.upstreamEndpoint` to the discovered
Glance image endpoint (for example
`http://glance-api.openstack.svc.cluster.local:9292`) or leave it empty to let
openstacksdk discover it.

## What the CompositionDefinition does

`compositiondefinition.yaml` (`core.krateo.io/v1alpha1`) registers the published
chart with Krateo. From it, core-provider derives a `composition.krateo.io` API: the
Kind is the PascalCase of the CD name with hyphens dropped
(`openstack-glance-operator-kog` → `OpenstackGlanceOperatorKog`) and the apiVersion
comes from the chart version (`0.1.0` → `composition.krateo.io/v0-1-0`). Applying an
instance of that Kind installs the **operator layer** (the `RestDefinition`s and the
auth-bridge) — it does not create Glance images itself; you declare those with the
generated per-resource CRs ([usage](./usage.md)).
