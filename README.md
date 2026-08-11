<p align="center">
  <img src="docs/krateo-loves-glance.png" alt="Krateo loves OpenStack Glance" width="900"/>
</p>

# openstack-glance-operator-kog

## What is this

A Krateo Operator Generator (KOG) blueprint — a Helm chart plus a sibling
`CompositionDefinition` — that turns **OpenStack Glance (image v2)** resources into
native Kubernetes custom resources. No hand-written controller: each resource is a
curated OpenAPI 3.0 subset, handed to `oasgen-provider` via a `RestDefinition` and
reconciled by the generic `rest-dynamic-controller`.

| Kind | Glance API | verbs |
|------|------------|-------|
| `Image` | `/v2/images` | create (metadata) / get / delete |
| `ImageImport` | `POST /v2/images/{id}/import` | web-download import (single-fire) |
| `ImageMember` | `/v2/images/{id}/members` | share / get / unshare |

Two Glance realities shape it: there is **no update verb** (Glance image update is
JSON-Patch only, so change an image by delete + recreate), and **binary upload is out
of KOG's reach** (`PUT .../file` is octet-stream) — an `Image` creates only `queued`
metadata, and an `ImageImport` with `method: web-download` populates it from a URL to
reach `active`. A stateless openstacksdk **auth-bridge** proxy injects a fresh
auto-refreshing `X-Auth-Token` in front of Glance. See
[docs/overview.md](docs/overview.md).

## Install

Prerequisites: Krateo's `oasgen-provider` in the cluster and an admin `clouds.yaml`
in a Secret.

```bash
kubectl -n krateo-system create secret generic glance-clouds --from-file=clouds.yaml=clouds.yaml
helm upgrade --install glance-kog ./chart -n krateo-system \
  --set authBridge.upstreamEndpoint=http://glance-api.openstack.svc.cluster.local:9292
```

Or install through Krateo by applying the `CompositionDefinition`. Full walkthrough:
[docs/usage.md](docs/usage.md) and [docs/quickstart.md](docs/quickstart.md).

## Configure

The value surface is per-resource `RestDefinition` toggles plus the auth-bridge
knobs, fully typed by `chart/values.schema.json`. The one required input is
`authBridge.upstreamEndpoint` (the upstream Glance image endpoint; leave empty to let
openstacksdk discover it). See [docs/configuration.md](docs/configuration.md).

```yaml
restdefinitions:
  image:
    enabled: true
  imageimport:
    enabled: true
  imagemember:
    enabled: true
authBridge:
  cloudsSecret: glance-clouds
  osCloud: openstack
  upstreamEndpoint: ""
```

## Examples

- [examples/composition](examples/composition/README.md) — install the operator
  layer through a Krateo `CompositionDefinition`-derived `OpenstackGlanceOperatorKog`
  CR.
- `chart/samples/image-resources.yaml` — ready-to-edit day-2 CRs
  (`ImageConfiguration`, `Image`, `ImageImport`).

## Docs

- [docs/index.md](docs/index.md) — the doc bundle map
- [docs/overview.md](docs/overview.md) — the KOG pipeline and the auth-bridge design
- [docs/usage.md](docs/usage.md) — install and drive the operator
- [docs/configuration.md](docs/configuration.md) — the whole value surface
- [docs/api.md](docs/api.md) — the CompositionDefinition CRD and the generated Glance CRDs
- [docs/examples.md](docs/examples.md) — the runnable examples
- [docs/release.md](docs/release.md) — how a release ships
- [docs/log.md](docs/log.md) — curated history
- [docs/quickstart.md](docs/quickstart.md) — the short end-to-end path
- [docs/llms.txt](docs/llms.txt) — the LLM doc index

## Develop & release

`security.yml` runs the shared security workflow and `lint.yaml` runs the shared
`lint-docs` documentation-standard check on every PR. A plain-SemVer tag (`X.Y.Z`,
no `v` prefix) matching `chart/Chart.yaml`'s `version` publishes the chart to
`oci://ghcr.io/krateo-blueprints/charts/openstack-glance-operator-kog` via
`release-chart.yaml`; then bump `compositiondefinition.yaml`'s `spec.chart.version`.
Details in [docs/release.md](docs/release.md).

## License

Apache-2.0 — see [LICENSE](LICENSE).
