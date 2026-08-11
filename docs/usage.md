---
type: Usage
title: openstack-glance-operator-kog — usage
description: How to install the Glance KOG operator and drive it — create an Image (metadata), populate it with a web-download ImageImport, and share it with an ImageMember.
resource: oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog
tags: [krateo, kog, glance, install, image-import]
timestamp: 2026-08-11T00:00:00Z
---

# Usage

## Prerequisites

Krateo's KOG provider (`oasgen-provider`) in the cluster:

```console
$ helm repo add krateo https://charts.krateo.io && helm repo update
$ helm upgrade --install oasgen-provider krateo/oasgen-provider -n krateo-system --create-namespace
```

An admin `clouds.yaml` for your OpenStack, stored in a Secret the auth-bridge reads:

```console
$ kubectl -n krateo-system create secret generic glance-clouds --from-file=clouds.yaml=clouds.yaml
```

## Install the operator

Point the auth-bridge at your Glance image endpoint (or leave it to openstacksdk
discovery), then install the chart:

```console
$ helm upgrade --install glance-kog ./chart -n krateo-system \
    --set authBridge.upstreamEndpoint=http://glance-api.openstack.svc.cluster.local:9292
$ kubectl -n krateo-system wait restdefinition/glance-kog-image --for=condition=Ready --timeout=300s
```

This installs the **operator layer** — the per-resource `RestDefinition`s and the
auth-bridge proxy. It does not create Glance images; you declare those with the
generated CRs below.

You can also install the same layer through Krateo by applying the
`CompositionDefinition` ([examples](./examples.md)).

## Create an image and populate it

An `Image` creates the metadata (status `queued`). An `ImageImport` with
`method: web-download` tells Glance to fetch the data from a URL — the KOG-friendly
way to get an `active` image (the binary `PUT .../file` upload is octet-stream, out
of KOG's reach).

The per-resource CRs reference a `<Kind>Configuration` that names the auth secret;
the auth-bridge injects the real token, so the token value is a placeholder:

```console
$ kubectl -n krateo-system create secret generic glance-token --from-literal=token=managed-by-proxy
```

```yaml
apiVersion: image.openstack.krateo.io/v1alpha1
kind: ImageConfiguration
metadata:
  name: glance-config
  namespace: krateo-system
spec:
  authentication:
    bearer:
      tokenRef:
        name: glance-token
        namespace: krateo-system
        key: token
---
apiVersion: image.openstack.krateo.io/v1alpha1
kind: Image
metadata:
  name: kog-demo-image
  namespace: krateo-system
spec:
  configurationRef:
    name: glance-config
    namespace: krateo-system
  name: kog-demo-image
  disk_format: qcow2
  container_format: bare
  visibility: private
```

Read the image id off the `Image` status, then start a web-download import:

```console
$ IMGID=$(kubectl -n krateo-system get image.image.openstack.krateo.io kog-demo-image -o jsonpath='{.status.id}')
```

```yaml
apiVersion: image.openstack.krateo.io/v1alpha1
kind: ImageImport
metadata:
  name: kog-demo-import
  namespace: krateo-system
spec:
  configurationRef:
    name: glance-config-import
    namespace: krateo-system
  image_id: "<the IMGID value>"
  method:
    name: web-download
    uri: "https://download.cirros-cloud.net/0.6.2/cirros-0.6.2-x86_64-disk.img"
```

Once the web-download completes the image is **Active** in Horizon under
**Compute → Images**. A ready-to-edit version of all of these CRs ships in
`chart/samples/image-resources.yaml`.

## Share an image

Enable `imagemember` (`restdefinitions.imagemember.enabled=true`) and declare an
`ImageMember` to share an image with another project:

```yaml
apiVersion: image.openstack.krateo.io/v1alpha1
kind: ImageMember
metadata:
  name: kog-demo-share
  namespace: krateo-system
spec:
  configurationRef:
    name: glance-config
    namespace: krateo-system
  image_id: "<the IMGID value>"
  member: "<target project id>"
```

Deleting the `ImageMember` unshares the image. A member's `status` (accept / reject)
is set by the **target** project and is out of scope here.

## Change or delete an image

There is no update verb (Glance image update is JSON-Patch only). To change an
image, delete the `Image` CR and re-create it with the new spec. Deleting the
`Image` deletes it in Glance.
