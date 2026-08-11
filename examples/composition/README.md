---
type: Example
title: composition — install the Glance KOG operator via a CompositionDefinition
description: A CompositionDefinition-driven install of the OpenStack Glance KOG blueprint — the per-resource RestDefinitions plus the auth-bridge — configured through the composition spec.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, glance, composition, example]
timestamp: 2026-08-11T00:00:00Z
---

# composition

`composition.yaml` installs the Glance KOG **operator layer** through Krateo instead
of a raw `helm install`. Applying it deploys the per-resource `RestDefinition`s
(`Image` / `ImageImport` / `ImageMember`) and the stateless Keystone auth-bridge
proxy that injects a fresh `X-Auth-Token` in front of Glance.

It does **not** create Glance images itself. Once the operator is running and the
generated CRDs exist, declare actual images with the per-resource CRs
(`ImageConfiguration` / `Image` / `ImageImport` / `ImageMember`) shown in
[usage](../../docs/usage.md) and shipped in `chart/samples/image-resources.yaml`.

## The composition

The CR's Kind and apiVersion are derived by core-provider from the
`CompositionDefinition`: group `composition.krateo.io`, version from the chart
version `0.1.0` → `v0-1-0`, and Kind from the CD name with hyphens dropped →
`OpenstackGlanceOperatorKog`. Its `spec` mirrors the chart values
([configuration](../../docs/configuration.md)):

```yaml
apiVersion: composition.krateo.io/v0-1-0
kind: OpenstackGlanceOperatorKog
metadata:
  name: openstack-glance-operator-kog
  namespace: openstack
spec:
  authBridge:
    upstreamEndpoint: http://glance-api.openstack.svc.cluster.local:9292
    cloudsSecret: glance-clouds
    osCloud: openstack
  restdefinitions:
    image:
      enabled: true
    imageimport:
      enabled: true
    imagemember:
      enabled: false
```

## Run it

Prerequisite: a Secret with your `clouds.yaml` in the target namespace, e.g.

```console
$ kubectl create secret generic glance-clouds --from-file=clouds.yaml=clouds.yaml -n openstack
```

Then apply the composition:

```console
$ kubectl apply -f examples/composition/composition.yaml
```

`upstreamEndpoint` is the key input — the upstream Glance image endpoint discovered
from the Keystone catalog; leave it empty to let openstacksdk discover it. Flip
`restdefinitions.imagemember.enabled` to `true` to manage image sharing.
