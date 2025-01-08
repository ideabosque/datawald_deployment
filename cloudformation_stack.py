#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = "bibow"

import importlib
import json
import os
import sys
import zipfile
from datetime import date, datetime
from decimal import Decimal
from time import sleep

import boto3
import dotenv
from botocore.configloader import load_config
from botocore.exceptions import ClientError

# Look for a .env file
if len(sys.argv) == 3:
    dotenv.load_dotenv(sys.argv[-2])
else:
    dotenv.load_dotenv(".env")

lambda_config = json.load(
    open(
        f"{os.path.abspath(os.path.dirname(__file__))}/lambda_config.json",
        "r",
    )
)
root_path = os.getenv("root_path")
site_packages = os.getenv("site_packages")

import logging

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        # logging.FileHandler("cloudformation_stack.log"),
        logging.StreamHandler(sys.stdout)
    ],
)
logger = logging.getLogger()


def execute_hook(lambda_function_name, function_config, hook_function_name):
    if not function_config.get("hooks") or not function_config.get("endpoint_id"):
        return

    packages = function_config.get("hooks", {}).get("packages")
    if type(packages) is not list or len(packages) < 1:
        return
    print(packages)
    events = function_config.get("hooks", {}).get("events")
    if type(events) is not dict or len(events) < 1:
        return

    hooks = events.get(hook_function_name)
    if type(hooks) is not list or len(hooks) < 1:
        return

    requires = ["package_name", "function_name"]
    for hook in hooks:
        if requires != [v for v in requires if v in hook.keys()]:
            continue

        print(hook.get("package_name"))
        spec = importlib.util.find_spec(hook.get("package_name"))

        if spec is None:
            continue

        agent = importlib.import_module(hook.get("package_name"))
        if hook.get("class_name"):
            agent = getattr(agent, hook.get("class_name"))

        agent = getattr(agent, hook.get("function_name"))
        if callable(agent):
            agent(
                str(lambda_function_name).strip(),
                str(function_config.get("endpoint_id")).strip(),
                str(function_config.get("area", "core")).strip(),
                packages,
            )
    logger.info(f"Execute {hook_function_name} hooks.")


# Helper class to convert a DynamoDB item to JSON.
class JSONEncoder(json.JSONEncoder):
    def default(self, o):  # pylint: disable=method-hidden
        if isinstance(o, Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        elif isinstance(o, (datetime, date)):
            return o.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(o, (bytes, bytearray)):
            return str(o)
        else:
            return super(JSONEncoder, self).default(o)


class CloudformationStack(object):
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
        for root, dirs, files in os.walk(dirpath):
            # if os.path.basename(root)[0] == '.':
            # continue  # skip hidden directories
            dirname = root.replace(basedir, "")
            for f in files:
                # if f[-1] == '~' or (f[0] == '.' and f != '.htaccess'):
                # skip backup files and all hidden files except .htaccess
                # continue
                if not is_package:
                    dirname = ""
                fzip.write(root + "/" + f, dirname + "/" + f)

    def pack_aws_lambda(self, lambda_file, base, packages, package_files=[], files={}):
        fzip = zipfile.ZipFile(lambda_file, "w", zipfile.ZIP_DEFLATED)
        base = f"{root_path}/{base}"
        self.zip_dir(base, fzip, is_package=False)
        for package in packages:
            self.zip_dir(
                f"{site_packages}/{package}",
                fzip,
            )
        for f in package_files:
            fzip.write(
                f"{site_packages}/{f}",
                f,
            )
        for f, path in files.items():
            fzip.write(f"{path}/{f}", f)
        fzip.close()

    def pack_aws_lambda_layer(self, layer_file, packages, package_files=[], files={}):
        fzip = zipfile.ZipFile(layer_file, "w", zipfile.ZIP_DEFLATED)
        for package in packages:
            self.zip_dir(
                f"{site_packages}/{package}",
                fzip,
            )
        for f in package_files:
            fzip.write(
                f"{site_packages}/{f}",
                f,
            )
        for f, path in files.items():
            fzip.write(f"{path}/{f}", f)
        fzip.close()

    def upload_aws_s3_bucket(self, lambda_file, bucket):
        f = open(lambda_file, "rb")
        self.aws_s3.Bucket(bucket).put_object(Key=lambda_file, Body=f)

    # Check if the stack exists.
    def _stack_exists(self, stack_name):
        try:
            response = self.aws_cloudformation.describe_stacks(StackName=stack_name)
            for stack in response["Stacks"]:
                if stack["StackStatus"] == "DELETE_COMPLETE":
                    continue
                if stack_name == stack["StackName"]:
                    return True
            return False
        except ClientError as e:
            if (
                e.response["Error"]["Message"]
                == f"Stack with id {stack_name} does not exist"
            ):
                return False
            raise

    # Retrieve the last version of the object in a S3 bucket.
    def _get_object_last_version(self, s3_key):
        object_summary = self.aws_s3.ObjectSummary(os.getenv("bucket"), s3_key)
        return object_summary.get()["VersionId"]

    def _get_layer_version_arn(self, layer_name):
        response = self.aws_lambda.list_layer_versions(LayerName=layer_name)
        assert (
            len(response["LayerVersions"]) > 0
        ), f"Cannot find the lambda layer ({layer_name})."

        return response["LayerVersions"][0]["LayerVersionArn"]

    @classmethod
    def deploy(cls):
        cf = cls()
        stack_name = sys.argv[-1]
        template_path = f"{stack_name}.json"

        # Load the CloudFormation template
        with open(template_path, "r") as file:
            template = json.load(file)

        # Collect Lambda functions and layers from the template
        functions, layers = cls._collect_resources(template)

        # Package and upload Lambda functions
        cls._process_lambda_functions(cf, functions)

        # Package and upload Lambda layers
        cls._process_lambda_layers(cf, layers)

        # Update the CloudFormation stack
        cls._update_cloudformation_stack(cf, stack_name, template)

        # Monitor the stack status until it is no longer "IN_PROGRESS"
        cls._monitor_stack_status(cf, stack_name)

        # Execute hooks on deploy
        for name, function_config in lambda_config["functions"].items():
            if name not in functions:
                continue

            execute_hook(
                lambda_function_name=name,
                function_config=function_config,
                hook_function_name=sys._getframe().f_code.co_name,
            )

    @staticmethod
    def _collect_resources(template):
        functions = []
        layers = []
        for key, value in template["Resources"].items():
            resource_type = value["Type"]
            properties = value["Properties"]

            if resource_type == "AWS::Lambda::Function":
                functions.append(properties["FunctionName"])
            elif resource_type == "AWS::Lambda::LayerVersion":
                layers.append(properties["LayerName"])
        return functions, layers

    @classmethod
    def _process_lambda_functions(cls, cf, functions):
        for name, funct in lambda_config["functions"].items():
            if name not in functions:
                continue

            lambda_file = f"{name}.zip"
            cf.pack_aws_lambda(
                lambda_file,
                funct["base"],
                funct["packages"],
                package_files=funct["package_files"],
                files=funct["files"],
            )
            cf.upload_aws_s3_bucket(lambda_file, os.getenv("bucket"))
            logger.info(f"Uploaded the Lambda package ({name}).")

    @classmethod
    def _process_lambda_layers(cls, cf, layers):
        for name, layer in lambda_config["layers"].items():
            if name not in layers:
                continue

            layer_file = f"{name}.zip"
            cf.pack_aws_lambda_layer(
                layer_file,
                layer["packages"],
                package_files=layer["package_files"],
                files=layer["files"],
            )
            cf.upload_aws_s3_bucket(layer_file, os.getenv("bucket"))
            logger.info(f"Uploaded the Lambda layer package ({name}).")

    @classmethod
    def _update_cloudformation_stack(cls, cf, stack_name, template):
        # Update properties for resources in the template
        cls._update_template_properties(cf, template)

        # Prepare stack parameters
        params = {
            "StackName": stack_name,
            "TemplateBody": json.dumps(template, indent=4),
            "Capabilities": ["CAPABILITY_NAMED_IAM"],
            "Tags": [{"Key": "autostack", "Value": "true"}],
            "Parameters": [],
        }

        # Create or update the stack
        if cf._stack_exists(stack_name):
            response = cf.aws_cloudformation.update_stack(**params)
        else:
            response = cf.aws_cloudformation.create_stack(**params)

        logger.info(json.dumps(response, indent=4, cls=JSONEncoder, ensure_ascii=False))

    @staticmethod
    def _update_template_properties(cf, template):
        for key, value in template["Resources"].items():
            resource_type = value["Type"]
            properties = value["Properties"]

            if resource_type == "AWS::Lambda::Function":
                function_name = properties["FunctionName"]
                function_file = f"{function_name}.zip"
                function_version = f"{function_name}_version"

                properties["Layers"] = [
                    (
                        layer
                        if isinstance(layer, dict)
                        else cf._get_layer_version_arn(layer)
                    )
                    for layer in properties["Layers"]
                ]
                properties["Code"] = {
                    "S3Bucket": os.getenv("bucket"),
                    "S3ObjectVersion": os.getenv(
                        function_version, cf._get_object_last_version(function_file)
                    ),
                    "S3Key": function_file,
                }
                properties["Environment"]["Variables"] = {
                    k: os.getenv(k, v)
                    for k, v in properties["Environment"]["Variables"].items()
                }
                if os.getenv("runtime"):
                    properties["Runtime"] = os.getenv("runtime")
                if os.getenv("security_group_ids") and os.getenv("subnet_ids"):
                    properties["VpcConfig"] = {
                        "SecurityGroupIds": os.getenv("security_group_ids").split(","),
                        "SubnetIds": os.getenv("subnet_ids").split(","),
                    }
                if os.getenv("efs_access_point") and properties["Environment"][
                    "Variables"
                ].get("EFSMOUNTPOINT"):
                    properties["FileSystemConfigs"] = [
                        {
                            "Arn": {
                                "Fn::Sub": "arn:aws:elasticfilesystem:${AWS::Region}:${AWS::AccountId}:access-point/"
                                + os.getenv("efs_access_point")
                            },
                            "LocalMountPath": os.getenv("efs_local_mount_path"),
                        }
                    ]
            elif resource_type == "AWS::Lambda::LayerVersion":
                layer_name = properties["LayerName"]
                layer_file = f"{layer_name}.zip"
                layer_version = f"{layer_name}_version"
                properties["Content"] = {
                    "S3Bucket": os.getenv("bucket"),
                    "S3ObjectVersion": os.getenv(
                        layer_version, cf._get_object_last_version(layer_file)
                    ),
                    "S3Key": layer_file,
                }
            elif resource_type == "AWS::IAM::Role":
                if properties["RoleName"] == "silvaengine_exec" and os.getenv(
                    "iam_role_name"
                ):
                    properties["RoleName"] = os.getenv("iam_role_name")
                elif "silvaengine_microcore" in properties["RoleName"] and os.getenv(
                    "microcore_iam_role_name"
                ):
                    properties["RoleName"] = os.getenv("microcore_iam_role_name")

    @classmethod
    def _monitor_stack_status(cls, cf, stack_name):
        stack = cf.aws_cloudformation.describe_stacks(StackName=stack_name)["Stacks"][0]
        while "IN_PROGRESS" in stack["StackStatus"]:
            logger.info(
                json.dumps(
                    stack["StackStatus"], indent=4, cls=JSONEncoder, ensure_ascii=False
                )
            )
            sleep(5)
            stack = cf.aws_cloudformation.describe_stacks(StackName=stack_name)[
                "Stacks"
            ][0]

        logger.info(
            json.dumps(
                stack["StackStatus"], indent=4, cls=JSONEncoder, ensure_ascii=False
            )
        )


if __name__ == "__main__":
    CloudformationStack.deploy()
