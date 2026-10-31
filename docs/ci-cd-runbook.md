# CI/CD and Blue-Green Deployment Runbook

## Pipeline

Pushes to `main` build five immutable Docker images in parallel and publish both
the Git commit SHA and `latest` tags to Docker Hub. The deployment job obtains
short-lived AWS credentials through GitHub OIDC, connects to EKS, deploys the
inactive colour, waits for readiness, switches the stable Kubernetes Service,
runs an in-cluster health check, and then scales the previous colour to zero.

The public ALB always targets the stable Services, so switching pod selectors
does not change the public endpoint. A failed health check restores the previous
selector before the workflow exits.

## Required GitHub configuration

Repository variables:

- `DOCKERHUB_USERNAME`
- `APP_BASE_URL`, for example `http://villa-agency-alb-...amazonaws.com`

Repository secrets:

- `DOCKERHUB_TOKEN`
- `AWS_GITHUB_ACTIONS_ROLE_ARN`

The AWS role must trust only the intended GitHub repository and branch through
OIDC. Map the role to the EKS group `villa-agency-deployers`, then apply
`kubernetes/ci-cd-rbac.yaml` once as a cluster administrator.

## Deployment verification

```bash
kubectl get services -n villa-agency -o custom-columns=NAME:.metadata.name,ACTIVE:.spec.selector.app
kubectl get deployments -n villa-agency
kubectl get pods -n villa-agency --show-labels
```

During a release, both colours are available before the Service switch. After
the smoke test passes, the old colour remains defined but is scaled to zero.

## Manual rollback

Choose the previous colour and run, for example:

```bash
scripts/blue-green-rollback.sh \
  villa-frontend villa-frontend-service blue / villa-agency
```

The rollback script scales the selected colour, waits for readiness, switches
the Service, verifies it through the cluster network, and scales down the
replaced colour.
