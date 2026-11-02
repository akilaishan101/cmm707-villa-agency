#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: $0 <application> <service> <blue|green> <health-path> [namespace]" >&2
  exit 64
fi

application="$1"
service="$2"
target_colour="$3"
health_path="$4"
namespace="${5:-villa-agency}"

if [[ "$target_colour" != "blue" && "$target_colour" != "green" ]]; then
  echo "Target colour must be blue or green" >&2
  exit 64
fi

current_label="$(kubectl get service "$service" \
  --namespace "$namespace" \
  --output jsonpath='{.spec.selector.app}')"
target_deployment="${application}-${target_colour}"

kubectl scale deployment "$target_deployment" \
  --namespace "$namespace" \
  --replicas="${DEPLOYMENT_REPLICAS:-2}"

kubectl rollout status deployment/"$target_deployment" \
  --namespace "$namespace" \
  --timeout=5m

kubectl patch service "$service" \
  --namespace "$namespace" \
  --type=merge \
  --patch="{\"spec\":{\"selector\":{\"app\":\"$target_deployment\"}}}"

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
  echo "Rollback smoke test failed; restoring service $service to $current_label" >&2
  kubectl patch service "$service" \
    --namespace "$namespace" \
    --type=merge \
    --patch="{\"spec\":{\"selector\":{\"app\":\"$current_label\"}}}"
  kubectl scale deployment "$target_deployment" \
    --namespace "$namespace" \
    --replicas=0
  exit 1
fi

if kubectl get deployment "$current_label" \
  --namespace "$namespace" > /dev/null 2>&1; then
  kubectl scale deployment "$current_label" \
    --namespace "$namespace" \
    --replicas=0
fi

echo "Rollback complete: $service now routes to $target_deployment"
