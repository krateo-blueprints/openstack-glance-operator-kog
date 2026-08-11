---
type: Configuration
title: openstack-glance-operator-kog — configuration
description: The whole chart value surface — the per-resource RestDefinition toggles and the auth-bridge (Keystone-auth proxy) knobs — fully typed by values.schema.json.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, glance, values, auth-bridge]
timestamp: 2026-08-11T00:00:00Z
---

# Configuration

Everything is `chart/values.yaml`, typed by `chart/values.schema.json`. When installed
through a `CompositionDefinition`, the same keys are set under the composition's
`spec` ([examples](./examples.md)).

## Per-resource RestDefinitions (`restdefinitions.*`)

Each Glance resource is a `RestDefinition` you can toggle independently. All three
share the `image.openstack.krateo.io` group and default to enabled.

| key | default | effect |
|---|---|---|
| `restdefinitions.image.enabled` | `true` | Emit the `Image` `RestDefinition` (create metadata / get / delete). |
| `restdefinitions.image.resourceGroup` | `image.openstack.krateo.io` | API group for the generated `Image` CRD. |
| `restdefinitions.image.resourceKind` | `Image` | Kind of the generated `Image` CRD. |
| `restdefinitions.imageimport.enabled` | `true` | Emit the `ImageImport` `RestDefinition` (single-fire web-download import). |
| `restdefinitions.imageimport.resourceGroup` | `image.openstack.krateo.io` | API group for the generated `ImageImport` CRD. |
| `restdefinitions.imageimport.resourceKind` | `ImageImport` | Kind of the generated `ImageImport` CRD. |
| `restdefinitions.imagemember.enabled` | `true` | Emit the `ImageMember` `RestDefinition` (share / get / unshare). |
| `restdefinitions.imagemember.resourceGroup` | `image.openstack.krateo.io` | API group for the generated `ImageMember` CRD. |
| `restdefinitions.imagemember.resourceKind` | `ImageMember` | Kind of the generated `ImageMember` CRD. |

Glance v2 is flat JSON (no envelope), so the Kinds are unprefixed and there is no
Kind-vs-property collision; the `Image` resource carries no update verb because a
Glance image update is JSON-Patch only.

## The auth-bridge (`authBridge.*`)

A stateless Keystone-auth reverse proxy (openstacksdk). It authenticates with
`clouds.yaml`, discovers the Glance `image` endpoint, and injects a fresh
auto-refreshing `X-Auth-Token` in front of Glance. `upstreamEndpoint` is the one
required user input.

| key | default | effect |
|---|---|---|
| `authBridge.enabled` | `true` | Deploy the auth-bridge proxy (Deployment + Service + ConfigMap). |
| `authBridge.replicaCount` | `1` | Number of auth-bridge replicas. |
| `authBridge.cloudsSecret` | `glance-clouds` | Name of the Secret holding `clouds.yaml` (create with `kubectl create secret generic glance-clouds --from-file=clouds.yaml=clouds.yaml`). |
| `authBridge.osCloud` | `openstack` | Cloud name in `clouds.yaml` to authenticate as (`OS_CLOUD`). |
| `authBridge.serviceType` | `image` | Keystone catalog service type to discover the endpoint for (`SERVICE_TYPE`). For Glance this is `image`. |
| `authBridge.osInterface` | `internal` | Keystone catalog interface used when discovering the endpoint (`OS_INTERFACE`): `internal`, `public` or `admin`. |
| `authBridge.upstreamEndpoint` | `""` | **The key input.** The upstream Glance image endpoint (e.g. `http://glance-api.openstack.svc.cluster.local:9292`). Leave empty to let openstacksdk discover it from the Keystone catalog. |
| `authBridge.image.repository` | `quay.io/airshipit/openstack-client` | Proxy container image. |
| `authBridge.image.tag` | `2026.1-ubuntu_noble` | Proxy image tag. |
| `authBridge.image.pullPolicy` | `IfNotPresent` | Proxy image pull policy. |
| `authBridge.service.type` | `ClusterIP` | Service type exposing the proxy in-cluster. |
| `authBridge.service.port` | `8080` | Service port the proxy listens on (the OpenAPI `servers[0].url` points here). |
| `authBridge.resources.requests` | `cpu 20m / memory 64Mi` | Proxy container resource requests. |
| `authBridge.resources.limits` | `cpu 500m / memory 256Mi` | Proxy container resource limits. |
| `authBridge.podAnnotations` | `{}` | Annotations added to the proxy pod. |
| `authBridge.nodeSelector` | `{}` | Node selector for the proxy pod. |
| `authBridge.tolerations` | `[]` | Tolerations for the proxy pod. |
| `authBridge.affinity` | `{}` | Affinity rules for the proxy pod. |

## ServiceAccount and naming

| key | default | effect |
|---|---|---|
| `serviceAccount.create` | `false` | Create a ServiceAccount for the release. |
| `serviceAccount.name` | `""` | Name of the ServiceAccount to use (generated if empty and `create` is true). |
| `nameOverride` | `""` | Override the chart name used in resource names. |
| `fullnameOverride` | `""` | Override the fully qualified app name used in resource names. |
