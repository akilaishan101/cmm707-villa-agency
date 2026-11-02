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

smoke_pod="rollback-${target_colour}-$(date +%s)"
smoke_phase="CreateFailed"

if kubectl run "$smoke_pod" \
  --namespace "$namespace" \
  --image=curlimages/curl:8.12.1 \
  --restart=Never \
  --command -- \
  curl -fsS "http://$service$health_path"; then
  smoke_phase="Pending"
  for attempt in $(seq 1 60); do
    smoke_phase="$(kubectl get pod "$smoke_pod" \
      --namespace "$namespace" \
      --output jsonpath='{.status.phase}' 2>/dev/null || true)"
    if [[ "$smoke_phase" == "Succeeded" || "$smoke_phase" == "Failed" ]]; then
      break
    fi
    sleep 2
  done
fi

kubectl logs "$smoke_pod" --namespace "$namespace" 2>/dev/null || true
kubectl delete pod "$smoke_pod" \
  --namespace "$namespace" \
  --ignore-not-found \
  --wait=false > /dev/null 2>&1 || true

if [[ "$smoke_phase" != "Succeeded" ]]; then
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
