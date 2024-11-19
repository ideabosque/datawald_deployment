echo "y" | pip uninstall monitor_engine && pip install git+https://github.com/ideabosque/monitor_engine.git#egg=monitor_engine
echo "y" | pip uninstall datawald_interface_engine && pip install git+https://github.com/ideabosque/datawald_interface_engine.git@main#egg=datawald_interface_engine
echo "y" | pip uninstall datawald_connector && pip install git+https://github.com/ideabosque/datawald_connector.git@main#egg=datawald_connector
echo "y" | pip uninstall datawald_agency && pip install git+https://github.com/ideabosque/datawald_agency.git@main#egg=datawald_agency
echo "y" | pip uninstall suitetalk_connector && pip install git+https://github.com/ideabosque/suitetalk_connector.git@main#egg=suitetalk_connector
echo "y" | pip uninstall datawald_nsagency && pip install git+https://github.com/ideabosque/datawald_nsagency.git@main#egg=datawald_nsagency
echo "y" | pip uninstall sqs_connector && pip install git+https://github.com/ideabosque/sqs_connector.git@main#egg=sqs_connector
echo "y" | pip uninstall datawald_sqsagency && pip install git+https://github.com/ideabosque/datawald_sqsagency.git@main#egg=datawald_sqsagency
echo "y" | pip uninstall dynamodb_connector && pip install git+https://github.com/ideabosque/dynamodb_connector.git@main#egg=dynamodb_connector
echo "y" | pip uninstall datawald_dynamodbagency && pip install git+https://github.com/ideabosque/datawald_dynamodbagency.git@main#egg=datawald_dynamodbagency
echo "y" | pip uninstall s3_connector && pip install git+https://github.com/ideabosque/s3_connector.git@main#egg=s3_connector
echo "y" | pip uninstall datawald_s3agency && pip install git+https://github.com/ideabosque/datawald_s3agency.git@main#egg=datawald_s3agency
echo "y" | pip uninstall hubspot_connector && pip install git+https://github.com/ideabosque/hubspot_connector.git@main#egg=hubspot_connector
echo "y" | pip uninstall datawald_hubspotagency && pip install git+https://github.com/ideabosque/datawald_hubspotagency.git@main#egg=datawald_hubspotagency
echo "y" | pip uninstall mage2_connector && pip install git+https://github.com/ideabosque/mage2_connector.git@main#egg=mage2_connector
echo "y" | pip uninstall datawald_mage2agency && pip install git+https://github.com/ideabosque/datawald_mage2agency.git@main#egg=datawald_mage2agency

python cloudformation_stack.py .env silvaengine-microcore-dw