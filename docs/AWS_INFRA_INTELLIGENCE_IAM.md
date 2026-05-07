# AWS IAM — Read-only for Infrastructure Intelligence

Attach a dedicated IAM user or role with **least privilege** read-only API access. The collector uses **explicit access keys** you store in the connector (encrypted at home). Do not use admin keys.

## Required actions (v0 collector)

| Service | Actions |
|---------|---------|
| EC2 | `ec2:DescribeInstances`, `ec2:DescribeVolumes`, `ec2:DescribeSecurityGroups`, `ec2:DescribeNatGateways` |
| ELB v2 | `elasticloadbalancing:DescribeLoadBalancers` |
| EKS | `eks:ListClusters`, `eks:DescribeCluster`, `eks:ListNodegroups`, `eks:DescribeNodegroup` |
| RDS | `rds:DescribeDBInstances` |
| Cost Explorer | `ce:GetCostAndUsage`, `ce:GetReservationCoverage`, `ce:GetSavingsPlansCoverage` |
| ECS | `ecs:ListClusters`, `ecs:ListServices`, `ecs:DescribeServices` |
| Lambda | `lambda:ListFunctions` |
| S3 | `s3:ListAllMyBuckets`, `s3:GetBucketLocation`, `s3:GetLifecycleConfiguration` |
| CloudWatch | `cloudwatch:GetMetricStatistics` |

Optional later: CloudWatch metrics, S3 ListBucket/public access checks, ECS/Lambda deep rightsizing.

## Example policy (tighten Resource to your account if desired)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudCostInfraIntelRead",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeNatGateways",
        "elasticloadbalancing:DescribeLoadBalancers",
        "eks:ListClusters",
        "eks:DescribeCluster",
        "eks:ListNodegroups",
        "eks:DescribeNodegroup",
        "rds:DescribeDBInstances",
        "ce:GetCostAndUsage",
        "ce:GetReservationCoverage",
        "ce:GetSavingsPlansCoverage",
        "ecs:ListClusters",
        "ecs:ListServices",
        "ecs:DescribeServices",
        "lambda:ListFunctions",
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetLifecycleConfiguration",
        "cloudwatch:GetMetricStatistics"
      ],
      "Resource": "*"
    }
  ]
}
```

## Connector JSON shape — static IAM user keys

```json
{
  "access_key_id": "AKIA...",
  "secret_access_key": "...",
  "session_token": null,
  "region": "us-east-1"
}
```

If `access_key_id` / `secret_access_key` are empty, the API uses the **stub** graph for demos (no live AWS calls).

## Connector JSON shape — STS AssumeRole

Use a **delegate** principal (IAM user or role with `sts:AssumeRole` on the target role) plus the role to assume. You can put delegate keys in `delegate_*` or reuse `access_key_id` / `secret_access_key`.

```json
{
  "auth_mode": "assume_role",
  "region": "us-east-1",
  "role_arn": "arn:aws:iam::123456789012:role/CloudCostInfraReadOnly",
  "external_id": "optional-shared-secret",
  "role_session_name": "cloudcost-infra-intel",
  "delegate_access_key_id": "AKIA...",
  "delegate_secret_access_key": "..."
}
```

**Trust policy** on the read-only role must allow the delegate principal. Optionally require `sts:ExternalId` to match `external_id`.

**Delegate IAM policy** must include at least:

```json
{
  "Effect": "Allow",
  "Action": "sts:AssumeRole",
  "Resource": "arn:aws:iam::123456789012:role/CloudCostInfraReadOnly"
}
```

The **assumed** role should carry the EC2/ELB read-only policy from the table above.

Rotate delegate keys regularly and prefer short-lived credentials where possible.

## Customer questionnaire (for best cost optimization outcomes)

Ask these during onboarding so recommendations are actionable:

1. Which workloads are interruption-tolerant (Spot suitable) vs strictly On-Demand?
2. What current Savings Plans/Reserved Instance commitments exist?
3. Which EKS namespaces/services can scale down off-hours?
4. Which resources are compliance-bound and cannot change region/instance family?
5. Is CUR/Cost Explorer tag hygiene in place for team/service-level attribution?
