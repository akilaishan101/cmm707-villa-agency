#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <application> <service> <image> <health-path> [namespace]" >&2
  exit 64
fi

application="$1"
service="$2"
image="$3"
health_path="$4"
namespace="${5:-${KUBERNETES_NAMESPACE:-villa-agency}}"
replicas="${DEPLOYMENT_REPLICAS:-2}"

active_label="$(kubectl get service "$service" \
  --namespace "$namespace" \
  --output jsonpath='{.spec.selector.app}')"

case "$active_label" in
  "${application}-blue")
    target_colour="green"
    ;;
  "${application}-green")
    target_colour="blue"
    ;;
  *)
    target_colour="green"
    ;;
esac

source_deployment="$active_label"
if ! kubectl get deployment "$source_deployment" \
  --namespace "$namespace" > /dev/null 2>&1; then
  source_deployment="$application"
fi

target_deployment="${application}-${target_colour}"
target_label="$target_deployment"

echo "Deploying $image to inactive environment $target_colour"

kubectl get deployment "$source_deployment" \
  --namespace "$namespace" \
  --output json |
  jq \
    --arg name "$target_deployment" \
    --arg app "$target_label" \
    --arg colour "$target_colour" \
    --arg image "$image" \
    --argjson replicas "$replicas" '
      del(
        .metadata.creationTimestamp,
        .metadata.generation,
        .metadata.managedFields,
        .metadata.resourceVersion,
        .metadata.uid,
        .metadata.annotations["deployment.kubernetes.io/revision"],
        .status
      )
      | .metadata.name = $name
      | .metadata.labels.app = $app
      | .metadata.labels["deployment-slot"] = $colour
      | .spec.replicas = $replicas
      | .spec.selector.matchLabels.app = $app
      | .spec.template.metadata.labels.app = $app
      | .spec.template.metadata.labels["deployment-slot"] = $colour
      | .spec.template.metadata.annotations["villa-agency/image"] = $image
      | .spec.template.spec.containers[0].image = $image
    ' |
  kubectl apply --namespace "$namespace" --filename -

kubectl rollout status deployment/"$target_deployment" \
  --namespace "$namespace" \
  --timeout=5m

kubectl wait \
  --namespace "$namespace" \
  --for=condition=Ready \
  pod \
  --selector="app=$target_label" \
  --timeout=3m

kubectl patch service "$service" \
  --namespace "$namespace" \
  --type=merge \
  --patch="{\"spec\":{\"selector\":{\"app\":\"$target_label\"}}}"

smoke_succeeded=false
for attempt in 1 2 3 4 5 6; do
  if kubectl get --raw \
    "/api/v1/namespaces/$namespace/services/http:$service:80/proxy$health_path"; then
    echo
    smoke_succeeded=true
    break
  fi
  sleep 5
done

if [[ "$smoke_succeeded" != "true" ]]; then
  echo "Smoke test failed; restoring service $service to $active_label" >&2
  kubectl patch service "$service" \
    --namespace "$namespace" \
    --type=merge \
    --patch="{\"spec\":{\"selector\":{\"app\":\"$active_label\"}}}"
  kubectl scale deployment "$target_deployment" \
    --namespace "$namespace" \
    --replicas=0
  exit 1
fi

sleep "${ROLLBACK_WINDOW_SECONDS:-15}"

if [[ "$source_deployment" != "$target_deployment" ]]; then
  kubectl scale deployment "$source_deployment" \
    --namespace "$namespace" \
    --replicas=0
fi

echo "Service $service now routes to $target_label"
kubectl get service "$service" deployment/"$target_deployment" \
  --namespace "$namespace" \
  --output wide
