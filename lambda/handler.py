"""
每日扫描：对每个必需标签键分别搜索「可打标签但缺少该键」的资源，合并去重后批量打默认标签。
依赖：账号已启用 Resource Explorer，且所用视图包含 tags（IncludeProperty: tags）。
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Set

import boto3
from botocore.exceptions import ClientError

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

EXPLORER = boto3.client("resource-explorer-2")
TAGGING = boto3.client("resource-groups-taggingapi")

BATCH_SIZE = 20


def _required_keys():
    raw = os.environ.get("REQUIRED_TAG_KEYS", "Environment,Owner,Project")
    return [k.strip() for k in raw.split(",") if k.strip()]


def _default_tags():
    keys = _required_keys()
    tags = {}
    raw_defaults = os.environ.get("TAG_DEFAULTS_JSON")
    if raw_defaults:
        try:
            parsed = json.loads(raw_defaults)
            if isinstance(parsed, dict):
                tags.update({str(k): str(v) for k, v in parsed.items()})
        except json.JSONDecodeError:
            LOG.warning("TAG_DEFAULTS_JSON is not valid JSON, falling back to env vars")
    for key in keys:
        if key not in tags:
            env_name = "DEFAULT_" + key.upper().replace("-", "_")
            val = os.environ.get(env_name)
            if val:
                tags[key] = val
    extra = os.environ.get("EXTRA_TAGS_JSON")
    if extra:
        try:
            tags.update(json.loads(extra))
        except json.JSONDecodeError:
            LOG.warning("EXTRA_TAGS_JSON is not valid JSON, ignoring")
    out = {}
    missing = []
    for key in keys:
        if key in tags and tags[key]:
            out[key] = tags[key]
        else:
            missing.append(key)
    if missing:
        raise ValueError(
            "缺少必需标签键的默认值: " + ", ".join(missing)
        )
    out["AutoTagged"] = os.environ.get("AUTO_TAGGED_VALUE", "true")
    out["TaggedDate"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return out


def _search_all_arns(query: str, view_arn: Optional[str]) -> Set[str]:
    arns: Set[str] = set()
    token = None
    while True:
        kwargs = {"QueryString": query, "MaxResults": 1000}
        if view_arn:
            kwargs["ViewArn"] = view_arn
        if token:
            kwargs["NextToken"] = token
        try:
            resp = EXPLORER.search(**kwargs)
        except ClientError as e:
            LOG.error("Resource Explorer search failed: %s", e)
            raise
        for r in resp.get("Resources", []):
            arn = r.get("Arn") or r.get("ARN")
            if arn:
                arns.add(arn)
        token = resp.get("NextToken")
        if not token:
            break
    return arns


def _arns_missing_any_required(required: list, view_arn: Optional[str]) -> Set[str]:
    """对每个必需键查询 resourcetype.supports:tags -tag.key:<Key>，并合并（去重）。"""
    merged: Set[str] = set()
    for key in required:
        # 键名中的特殊字符需转义；常见键无特殊字符
        q = f"resourcetype.supports:tags -tag.key:{key}"
        found = _search_all_arns(q, view_arn)
        LOG.info("Query %r matched %d resources", q, len(found))
        merged |= found
    return merged


def _tag_in_batches(arns: list, tags: dict) -> None:
    for i in range(0, len(arns), BATCH_SIZE):
        batch = arns[i : i + BATCH_SIZE]
        try:
            resp = TAGGING.tag_resources(ResourceARNList=batch, Tags=tags)
        except ClientError as e:
            LOG.error("tag_resources failed for batch starting %s: %s", batch[0], e)
            continue
        failed = resp.get("FailedResourcesMap") or {}
        if failed:
            for arn, info in failed.items():
                LOG.warning("Tag failed %s: %s", arn, info)


def lambda_handler(event, context):
    del event, context
    required = _required_keys()
    if not required:
        LOG.error("REQUIRED_TAG_KEYS is empty")
        return {"statusCode": 400, "body": "REQUIRED_TAG_KEYS empty"}

    view_arn = os.environ.get("VIEW_ARN") or None
    if view_arn == "":
        view_arn = None

    try:
        tags = _default_tags()
    except ValueError as e:
        LOG.error("%s", e)
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}

    arns = sorted(_arns_missing_any_required(required, view_arn))
    LOG.info("Total unique ARNs to tag: %d", len(arns))
    if arns:
        _tag_in_batches(arns, tags)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {"taggedCandidateCount": len(arns), "requiredKeys": required}
        ),
    }
