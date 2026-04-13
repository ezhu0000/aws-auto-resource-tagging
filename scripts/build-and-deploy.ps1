#Requires -Version 5.1
<#
  将 lambda/handler.py 打成 zip，上传到指定 S3 桶，并部署/更新 CloudFormation 堆栈。
  用法示例:
    .\build-and-deploy.ps1 -BucketName my-artifacts-bucket -StackName auto-map-tag -Region ap-east-1
#>
param(
    [Parameter(Mandatory = $true)]
    [string] $BucketName,

    [string] $ObjectKey = "auto-map-tag/handler.zip",

    [string] $StackName = "auto-map-tag",

    [string] $Region = "ap-east-1",

    [string] $TemplateFile = (Join-Path $PSScriptRoot "..\cloudformation\auto-tagging.yaml")
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$zipPath = Join-Path $env:TEMP "auto-map-tag-handler.zip"
$handler = Join-Path $root "lambda\handler.py"

if (-not (Test-Path $handler)) {
    throw "找不到 $handler"
}

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $handler -DestinationPath $zipPath -Force

aws s3 cp $zipPath "s3://$BucketName/$ObjectKey" --region $Region

aws cloudformation deploy `
    --template-file $TemplateFile `
    --stack-name $StackName `
    --parameter-overrides `
        ArtifactBucketName=$BucketName `
        ArtifactObjectKey=$ObjectKey `
    --capabilities CAPABILITY_NAMED_IAM `
    --region $Region

Write-Host "完成。堆栈: $StackName，区域: $Region"
