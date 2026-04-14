# 自动打标签部署说明


## 在 AWS CloudShell 部署

1. 在 CloudShell 克隆仓库：

```bash
git clone https://github.com/ezhu0000/aws-auto-resource-tagging.git
cd aws-auto-resource-tagging
```

2. 部署堆栈：

```bash
# 注意：你可能需要传入自己的 RequiredTagMapJson 参数。
aws cloudformation deploy \
  --template-file auto-tagging.yaml \
  --stack-name auto-map-tag \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides RequiredTagMapJson='{"TagOwner":"你的值"}'
```

3. （可选）传入自定义参数：

```bash
aws cloudformation deploy \
  --template-file auto-tagging.yaml \
  --stack-name auto-map-tag \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    RequiredTagMapJson='{"TagOwner":"CDS-MAP","map-migrated":"migTPMCT-DEMO","Environment":"Prod"}' \
    ScheduleExpression='rate(1 day)' \
    CreateResourceExplorerSetup='true' \
    ResourceExplorerViewArn=''
```

## 附录：Lambda 会打标签的服务范围

Resource Explorer 可能匹配到账号内任意可打标资源，但 **Lambda 仅对下表中的 ARN `service` 段** 调用 Resource Groups Tagging API，其余匹配结果会跳过并记入日志（`allowlist skipped`），避免对未授权或未列出的服务产生大量 403。**KMS（`kms`）** 故意不在下表中：CMK 打标依赖密钥策略，本方案不尝试给 KMS 打标。**CloudFormation（`cloudformation`）** 亦不在白名单内：堆栈打标会牵涉 `UpdateStack` 等权限，本方案跳过。

ARN 格式为 `arn:partition:service:…`，下表第二列为该 **service** 取值（小写）。**EMR** 在 ARN 中为 `elasticmapreduce`，与 IAM 动作前缀 `emr` 不同。**API Gateway** 的 REST/HTTP 资源 ARN 中一般为 `apigateway`；堆栈中同时包含 `apigateway` 与 `apigatewayv2` 的打标权限以覆盖控制台 API。

| 服务（常用名） | ARN `service` |
|----------------|---------------|
| ACM | `acm` |
| API Gateway | `apigateway` |
| App Runner | `apprunner` |
| Athena | `athena` |
| AWS Backup | `backup` |
| CloudFront | `cloudfront` |
| CloudTrail | `cloudtrail` |
| CloudWatch（指标、告警等） | `cloudwatch` |
| CloudWatch Logs | `logs` |
| Amazon Connect | `connect` |
| DynamoDB | `dynamodb` |
| EC2（含 VPC、子网、安全组等） | `ec2` |
| ECR | `ecr` |
| ECS | `ecs` |
| EKS | `eks` |
| ElastiCache | `elasticache` |
| Elastic Beanstalk | `elasticbeanstalk` |
| EFS | `elasticfilesystem` |
| Elastic Load Balancing | `elasticloadbalancing` |
| EMR | `elasticmapreduce` |
| EventBridge | `events` |
| Firehose | `firehose` |
| FSx | `fsx` |
| Glue | `glue` |
| IAM（角色、策略等） | `iam` |
| Kinesis Data Streams | `kinesis` |
| Lambda | `lambda` |
| MemoryDB | `memorydb` |
| Amazon MQ | `mq` |
| MSK | `kafka` |
| OpenSearch Serverless | `aoss` |
| OpenSearch Service（托管域） | `es` |
| RAM | `ram` |
| RDS（含 Aurora 等） | `rds` |
| Redshift | `redshift` |
| S3 | `s3` |
| SageMaker | `sagemaker` |
| Secrets Manager | `secretsmanager` |
| SNS | `sns` |
| SQS | `sqs` |
| Step Functions | `states` |
| Systems Manager | `ssm` |
| WAFv2 | `wafv2` |

### 附录 A-1：Lambda 会跳过的 ARN（已知无法/不应统一打标）

在通过白名单之后、调用 Tagging API 之前会丢弃，并记日志 `skip_known_bad`：

| 规则 | 说明 |
|------|------|
| Athena `datacatalog/AwsDataCatalog` | 默认 Glue 数据目录在 Tagging API 中常报 `ResourceNotFoundException`，属伪资源表现。 |
| ElastiCache 含 `:user:` | 如 `user:default`，易触发服务相关角色/权限问题。 |
| MemoryDB 非 `cluster/` | 仅对 `…:cluster/名称` 打标；`user/`、`parametergroup/`、`acl/` 等统一 API 不支持或易失败。 |
| EventBridge 托管规则 | ARN 为 `…:rule/规则名`；规则名（小写）含 `connectcampaignsrule` 或 `managed.connect` 时跳过（`ManagedRuleException`）。 |
| S3 Storage Lens | ARN 含 `storage-lens` 的资源需单独权限模型，此处跳过。 |

**修改范围时**：请同时更新 `auto-tagging.yaml` 内 Lambda 中的 `ALLOWED_ARN_SERVICES`、`arn_skip_known_bad`、对应 IAM 的 `ServiceTagResourceDelegation` / `IamTagging` 与本附录，保持一致。
