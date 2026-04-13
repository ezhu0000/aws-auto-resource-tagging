# 自动打标签部署说明

该目录可直接上传到 GitHub。

## 在 AWS CloudShell 部署

1. 在 CloudShell 克隆你的仓库：

```bash
git clone <your-repo-url>
cd <your-repo>/deployment
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
