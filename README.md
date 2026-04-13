# 自动打标签部署说明

仓库地址已固定为：
`https://github.com/ezhu0000/aws-auto-resource-tagging.git`

## 在 AWS CloudShell 部署

1. 在 CloudShell 克隆仓库：

```bash
git clone https://github.com/ezhu0000/aws-auto-resource-tagging.git
cd aws-auto-resource-tagging
```

2. 部署堆栈：

```bash
aws cloudformation deploy \
  --template-file auto-tagging.yaml \
  --stack-name auto-map-tag \
  --capabilities CAPABILITY_NAMED_IAM
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
