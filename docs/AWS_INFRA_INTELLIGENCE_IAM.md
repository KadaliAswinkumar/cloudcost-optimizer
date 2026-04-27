# AWS IAM — Read-only for Infrastructure Intelligence

Attach a dedicated IAM user or role with **least privilege** read-only API access. The collector uses **explicit access keys** you store in the connector (encrypted at home). Do not use admin keys.

## Required actions (v0 collector)

| Service | Actions |
|---------|---------|
| EC2 | `ec2:DescribeInstances`, `ec2:DescribeVolumes`, `ec2:DescribeSecurityGroups`, `ec2:DescribeNatGateways` |
| ELB v2 | `elasticloadbalancing:DescribeLoadBalancers` |

Optional later: CloudWatch, Cost Explorer, S3 ListBucket (public access checks).

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
        "elasticloadbalancing:DescribeLoadBalancers"
      ],
      "Resource": "*"
    }
  ]
}
```

## Connector JSON shape

```json
{
  "access_key_id": "AKIA...",
  "secret_access_key": "...",
  "session_token": null,
  "region": "us-east-1"
}
```

If `access_key_id` / `secret_access_key` are empty, the API uses the **stub** graph for demos (no live AWS calls).

Cross-role (STS `AssumeRole`) is a follow-up; keep keys in a vault and rotate regularly.
