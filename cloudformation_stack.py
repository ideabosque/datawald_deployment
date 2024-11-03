#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import importlib
import json
import logging
import os
import sys
import zipfile
from datetime import date, datetime
from decimal import Decimal
from time import sleep

import boto3
import dotenv
from botocore.exceptions import ClientError

# Load environment variables from .env file
dotenv.load_dotenv(sys.argv[-2] if len(sys.argv) == 3 else ".env")

# Set up logging
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger()

# Load configuration
lambda_config_path = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), "lambda_config.json"
)
lambda_config = json.load(open(lambda_config_path, "r"))

# Environment variables
root_path = os.getenv("root_path")
site_packages = os.getenv("site_packages")
# functions = os.getenv("functions", "").split(",")
# layers = os.getenv("layers", "").split(",")


# Helper class to convert a DynamoDB item to JSON
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o) if o % 1 > 0 else int(o)
        elif isinstance(o, (datetime, date)):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(o, (bytes, bytearray)):
            return str(o)
        return super(JSONEncoder, self).default(o)


# Main CloudFormation Stack class
class CloudformationStack:
    def __init__(self):
        self.aws_cloudformation = boto3.client(
            "cloudformation",
            region_name=os.getenv("region_name"),
            aws_access_key_id=os.getenv("aws_access_key_id"),
            aws_secret_access_key=os.getenv("aws_secret_access_key"),
        )
        self.aws_s3 = boto3.resource(
            "s3",
            region_name=os.getenv("region_name"),
            aws_access_key_id=os.getenv("aws_access_key_id"),
            aws_secret_access_key=os.getenv("aws_secret_access_key"),
        )
        self.aws_lambda = boto3.client(
            "lambda",
            region_name=os.getenv("region_name"),
            aws_access_key_id=os.getenv("aws_access_key_id"),
            aws_secret_access_key=os.getenv("aws_secret_access_key"),
        )

    @staticmethod
    def zip_dir(dirpath, fzip, is_package=True):
        basedir = os.path.dirname(dirpath) + "/"
        for root, _, files in os.walk(dirpath):
            dirname = root.replace(basedir, "") if not is_package else ""
            for file in files:
                fzip.write(os.path.join(root, file), os.path.join(dirname, file))

    def pack_aws_lambda(self, lambda_file, base, packages, package_files=[], files={}):
        with zipfile.ZipFile(lambda_file, "w", zipfile.ZIP_DEFLATED) as fzip:
            self.zip_dir(f"{root_path}/{base}", fzip, is_package=False)
            for package in packages:
                self.zip_dir(f"{site_packages}/{package}", fzip)
            for file in package_files:
                fzip.write(f"{site_packages}/{file}", file)
            for file, path in files.items():
                fzip.write(os.path.join(path, file), file)

    def pack_aws_lambda_layer(self, layer_file, packages, package_files=[], files={}):
        with zipfile.ZipFile(layer_file, "w", zipfile.ZIP_DEFLATED) as fzip:
            for package in packages:
                self.zip_dir(f"{site_packages}/{package}", fzip)
            for file in package_files:
                fzip.write(f"{site_packages}/{file}", file)
            for file, path in files.items():
                fzip.write(os.path.join(path, file), file)

    def upload_aws_s3_bucket(self, lambda_file, bucket):
        with open(lambda_file, "rb") as file:
            self.aws_s3.Bucket(bucket).put_object(Key=lambda_file, Body=file)

    def _stack_exists(self, stack_name):
        try:
            response = self.aws_cloudformation.describe_stacks(StackName=stack_name)
            for stack in response["Stacks"]:
                if (
                    stack["StackStatus"] != "DELETE_COMPLETE"
                    and stack["StackName"] == stack_name
                ):
                    return True
            return False
        except ClientError as e:
            if "does not exist" in e.response["Error"]["Message"]:
                return False
            raise

    def _get_object_last_version(self, s3_key):
        object_summary = self.aws_s3.ObjectSummary(os.getenv("bucket"), s3_key)
        return object_summary.get()["VersionId"]

    def _get_layer_version_arn(self, layer_name):
        response = self.aws_lambda.list_layer_versions(LayerName=layer_name)
        if not response["LayerVersions"]:
            raise ValueError(f"Cannot find the lambda layer ({layer_name}).")
        return response["LayerVersions"][0]["LayerVersionArn"]

    @classmethod
    def deploy(cls):
        instance = cls()

        # Update or create CloudFormation stack
        stack_name = sys.argv[-1]
        template_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), f"{stack_name}.json"
        )
        template = json.load(open(template_path, "r"))

        functions = []
        layers = []
        for resource, value in template["Resources"].items():
            if value["Type"] == "AWS::Lambda::Function":
                functions.append(value["Properties"]["FunctionName"])
            elif value["Type"] == "AWS::Lambda::LayerVersion":
                layers.append(value["Properties"]["LayerName"])

        # Package and upload Lambda functions
        for name, function in lambda_config["functions"].items():
            if name not in functions:
                continue
            lambda_file = f"{name}.zip"
            instance.pack_aws_lambda(
                lambda_file,
                function["base"],
                function["packages"],
                package_files=function.get("package_files", []),
                files=function.get("files", {}),
            )
            instance.upload_aws_s3_bucket(lambda_file, os.getenv("bucket"))
            logger.info(f"Uploaded the Lambda package ({name}).")

        # Update Lambda and Layer configurations
        for resource, value in template["Resources"].items():
            if value["Type"] == "AWS::Lambda::Function":
                cls._update_lambda_function_resource(instance, value)
            elif value["Type"] == "AWS::Lambda::LayerVersion":
                cls._update_lambda_layer_resource(instance, value)
            elif value["Type"] == "AWS::IAM::Role" and os.getenv("iam_role_name"):
                value["Properties"]["RoleName"] = os.getenv("iam_role_name")

        # Package and upload Lambda layers
        for name, layer in lambda_config["layers"].items():
            if name not in layers:
                continue
            layer_file = f"{name}.zip"
            instance.pack_aws_lambda_layer(
                layer_file,
                layer["packages"],
                package_files=layer.get("package_files", []),
                files=layer.get("files", {}),
            )
            instance.upload_aws_s3_bucket(layer_file, os.getenv("bucket"))
            logger.info(f"Uploaded the Lambda layer package ({name}).")

        params = {
            "StackName": stack_name,
            "TemplateBody": json.dumps(template, indent=4),
            "Capabilities": ["CAPABILITY_NAMED_IAM"],
            "Tags": [{"Key": "autostack", "Value": "true"}],
            "Parameters": [],
        }

        response = (
            instance.aws_cloudformation.update_stack(**params)
            if instance._stack_exists(stack_name)
            else instance.aws_cloudformation.create_stack(**params)
        )
        logger.info(json.dumps(response, indent=4, cls=JSONEncoder, ensure_ascii=False))

        # Wait for stack to complete
        instance._wait_for_stack_completion(stack_name)

        # Execute hooks on deployment
        for name, function_config in lambda_config["functions"].items():
            if name in functions:
                execute_hook(name, function_config, sys._getframe().f_code.co_name)

    @staticmethod
    def _update_lambda_function_resource(instance, resource):
        function_name = resource["Properties"]["FunctionName"]
        function_file = f"{function_name}.zip"
        resource["Properties"]["Layers"] = [
            (
                instance._get_layer_version_arn(layer)
                if not isinstance(layer, dict)
                else layer
            )
            for layer in resource["Properties"]["Layers"]
        ]
        resource["Properties"]["Code"] = {
            "S3Bucket": os.getenv("bucket"),
            "S3ObjectVersion": os.getenv(
                function_name + "_version",
                instance._get_object_last_version(function_file),
            ),
            "S3Key": function_file,
        }
        resource["Properties"]["Environment"]["Variables"] = {
            k: os.getenv(k, v)
            for k, v in resource["Properties"]["Environment"]["Variables"].items()
        }
        if os.getenv("runtime"):
            resource["Properties"]["Runtime"] = os.getenv("runtime")
        if os.getenv("security_group_ids") and os.getenv("subnet_ids"):
            resource["Properties"]["VpcConfig"] = {
                "SecurityGroupIds": os.getenv("security_group_ids").split(","),
                "SubnetIds": os.getenv("subnet_ids").split(","),
            }
        if os.getenv("efs_access_point") and resource["Properties"]["Environment"][
            "Variables"
        ].get("EFSMOUNTPOINT"):
            resource["Properties"]["FileSystemConfigs"] = [
                {
                    "Arn": {
                        "Fn::Sub": "arn:aws:elasticfilesystem:${AWS::Region}:${AWS::AccountId}:access-point/"
                        + os.getenv("efs_access_point")
                    },
                    "LocalMountPath": os.getenv("efs_local_mount_path"),
                }
            ]

    @staticmethod
    def _update_lambda_layer_resource(instance, resource):
        layer_name = resource["Properties"]["LayerName"]
        layer_file = f"{layer_name}.zip"
        resource["Properties"]["Content"] = {
            "S3Bucket": os.getenv("bucket"),
            "S3ObjectVersion": os.getenv(
                layer_name + "_version", instance._get_object_last_version(layer_file)
            ),
            "S3Key": layer_file,
        }

    def _wait_for_stack_completion(self, stack_name):
        stack = self.aws_cloudformation.describe_stacks(StackName=stack_name)["Stacks"][
            0
        ]
        while "IN_PROGRESS" in stack["StackStatus"]:
            logger.info(
                json.dumps(
                    stack["StackStatus"], indent=4, cls=JSONEncoder, ensure_ascii=False
                )
            )
            sleep(5)
            stack = self.aws_cloudformation.describe_stacks(StackName=stack_name)[
                "Stacks"
            ][0]
        logger.info(
            json.dumps(
                stack["StackStatus"], indent=4, cls=JSONEncoder, ensure_ascii=False
            )
        )


def execute_hook(lambda_function_name, function_config, hook_function_name):
    if not function_config.get("hooks") or not function_config.get("endpoint_id"):
        return

    packages = function_config["hooks"].get("packages", [])
    events = function_config["hooks"].get("events", {})
    hooks = events.get(hook_function_name, [])

    for hook in hooks:
        if all(k in hook for k in ["package_name", "function_name"]):
            spec = importlib.util.find_spec(hook["package_name"])
            if spec:
                agent = importlib.import_module(hook["package_name"])
                if "class_name" in hook:
                    agent = getattr(agent, hook["class_name"])
                agent = getattr(agent, hook["function_name"])
                if callable(agent):
                    agent(
                        lambda_function_name.strip(),
                        function_config["endpoint_id"].strip(),
                        packages,
                    )
    logger.info(f"Executed {hook_function_name} hooks.")


if __name__ == "__main__":
    CloudformationStack.deploy()
