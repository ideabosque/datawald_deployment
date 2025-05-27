#!/bin/bash

# Check for environment file argument
if [ -z "$1" ]; then
  echo "Usage: $0 <env_file_path>"
  exit 1
fi

ENV_FILE="$1"
BRANCH="${2:-main}"

echo "y" | pip uninstall silvaengine_resource && pip install git+https://github.com/ideabosque/silvaengine_resouces.git@$BRANCH#egg=silvaengine_resource
echo "y" | pip uninstall datawald_interface_engine && pip install git+https://github.com/ideabosque/datawald_interface_engine.git@$BRANCH#egg=datawald_interface_engine
echo "y" | pip uninstall datawald_connector && pip install git+https://github.com/ideabosque/datawald_connector.git@$BRANCH#egg=datawald_connector
echo "y" | pip uninstall datawald_agency && pip install git+https://github.com/ideabosque/datawald_agency.git@$BRANCH#egg=datawald_agency
echo "y" | pip uninstall suitetalk_connector && pip install git+https://github.com/ideabosque/suitetalk_connector.git@$BRANCH#egg=suitetalk_connector
echo "y" | pip uninstall datawald_nsagency && pip install git+https://github.com/ideabosque/datawald_nsagency.git@$BRANCH#egg=datawald_nsagency
echo "y" | pip uninstall sqs_connector && pip install git+https://github.com/ideabosque/sqs_connector.git@$BRANCH#egg=sqs_connector
echo "y" | pip uninstall datawald_sqsagency && pip install git+https://github.com/ideabosque/datawald_sqsagency.git@$BRANCH#egg=datawald_sqsagency
echo "y" | pip uninstall dynamodb_connector && pip install git+https://github.com/ideabosque/dynamodb_connector.git@$BRANCH#egg=dynamodb_connector
echo "y" | pip uninstall datawald_dynamodbagency && pip install git+https://github.com/ideabosque/datawald_dynamodbagency.git@$BRANCH#egg=datawald_dynamodbagency
echo "y" | pip uninstall s3_connector && pip install git+https://github.com/ideabosque/s3_connector.git@$BRANCH#egg=s3_connector
echo "y" | pip uninstall datawald_s3agency && pip install git+https://github.com/ideabosque/datawald_s3agency.git@$BRANCH#egg=datawald_s3agency
echo "y" | pip uninstall hubspot_connector && pip install git+https://github.com/ideabosque/hubspot_connector.git@$BRANCH#egg=hubspot_connector
echo "y" | pip uninstall datawald_hubspotagency && pip install git+https://github.com/ideabosque/datawald_hubspotagency.git@$BRANCH#egg=datawald_hubspotagency
echo "y" | pip uninstall mage2_connector && pip install git+https://github.com/ideabosque/mage2_connector.git@$BRANCH#egg=mage2_connector
echo "y" | pip uninstall datawald_mage2agency && pip install git+https://github.com/ideabosque/datawald_mage2agency.git@$BRANCH#egg=datawald_mage2agency

python cloudformation_stack.py "$ENV_FILE" silvaengine-microcore-dw