# DataWald Integration Framework

## Introduction

DataWald, a framework powered by SilvaEngine, is designed to streamline system integration with unparalleled flexibility. By enabling configurable data mapping, it efficiently processes and adapts data to meet diverse requirements. Built on a modular, microservices architecture, DataWald is highly scalable, making it easy to integrate and support a wide range of systems for seamless data flow and interoperability.

## Dataflow

### First Approach with AWS EventBridge

![First Approach with AWS EventBridge](/images/first_approach_with_eventbridge.png)

1. **EventBridge** triggers the data synchronization process by invoking the `retrieve_entities_from_source` function via the `silvaengine_agenttask` AWS Lambda function.
2. **Silvaengine_agenttask** calls `silvaengine_microcore_src`, a module structured around the core abstract module `datawald_agency` that is specifically configured to interact with the designated source system. Within this structure, `src_connector` manages direct communication with the source system, while `datawald_srcagency` operates as the business logic layer, orchestrating data retrieval processes.
3. **Silvaengine_microcore_src** then initiates data synchronization by calling the `insert_update_entities_to_target` function through the `datawald_interface_engine`, which facilitates the transition of data into the target system.
4. **Datawald_interface_engine** holds the synchronized data in a staging area, coordinating the entire synchronization task. It then uses AWS SQS to send a message to `silvaengine_task_queue`, which triggers the `insert_update_entities_to_target` function. Following this queue process, it dispatches the `sync_task` function to update the status of the synchronization task.
5. Upon receiving the queued message, **silvaengine_agenttask** activates `silvaengine_microcore_tgt`, which processes and prepares the data for integration into the target system. Once the data is processed, `silvaengine_microcore_tgt` updates the synchronization task status within `datawald_interface_engine` by calling `sync_task`.

This structured, layered workflow enables efficient and cohesive data integration and synchronization across source and target systems, maintaining data consistency and task tracking throughout the process.

### Second Approach with AWS SQS

![Second Approach with AWS SQS](/images/second_approach_with_sqs.png)

1. The **source system** initiates data synchronization by invoking the `datawald_interface_engine` with the data payload. This data is then sent to the AWS SQS `datawald_input_queue`, which automatically triggers the **silvaengine_agenttask** Lambda function.
2. **Silvaengine_agenttask** subsequently calls `silvaengine_microcore_sqs`, a module structured around the abstract base `datawald_agency` to interact with the specified source system. Within this framework, `datawald_sqsagency` operates as the business logic layer, managing data processing and preparation based on the queue input.
3. **Silvaengine_microcore_sqs** then synchronizes the data by invoking the `insert_update_entities_to_target` function through the `datawald_interface_engine`, setting up data for integration with the target system.
4. **Datawald_interface_engine** stores the synchronized data in a staging area and orchestrates the synchronization task. It then dispatches the `insert_update_entities_to_target` function via AWS SQS `silvaengine_task_queue`. Once this queue process completes, it triggers the `sync_task` function to update the task’s synchronization status.
5. Upon receiving the final queued message, **silvaengine_agenttask** initiates `silvaengine_microcore_tgt`, which processes and prepares the data for integration into the target system. After processing, `silvaengine_microcore_tgt` updates the synchronization task status by calling the `sync_task` function within `datawald_interface_engine`.

This layered and modular workflow ensures seamless data integration and synchronization between source and target systems, enabling efficient task management, data consistency, and traceability throughout the process.

## Detail of Modules

**Core Modules**

- [**datawald_interface_engine**](https://github.com/ideabosque/datawald_interface_engine): Serves as the central engine that orchestrates the entire data management framework.
- [**datawald_agency**](https://github.com/ideabosque/datawald_agency): Provides an abstract layer for system-specific modules, enabling streamlined data integration across different platforms.
- [**datawald_connector**](https://github.com/ideabosque/datawald_connector): Acts as a bridge between the datawald_interface_engine and external dataflows, facilitating seamless data communication.

**NetSuite Integration**

- [**datawald_nsagency**](https://github.com/ideabosque/datawald_nsagency): Processes NetSuite data, applying tailored business logic to meet operational requirements.
- [**suitetalk_connector**](https://github.com/ideabosque/suitetalk_connector): Communicates with NetSuite via SOAP and RESTful protocols to ensure effective data exchange.

**Magento 2 Integration**

- [**datawald_mage2agency**](https://github.com/ideabosque/datawald_dynamodbagency): Manages and processes data for Magento 2, embedding business logic to support e-commerce functions.
- [**mage2_connector**](https://github.com/ideabosque/mage2_connector): Connects to Magento 2 to enable efficient data transactions and synchronization.

**HubSpot Integration**

- [**datawald_hubspotagency**](https://github.com/ideabosque/datawald_hubspotagency): Processes and manages HubSpot data, integrating specific business logic for customer relationship workflows.
- [**hubspot_connector**](https://github.com/ideabosque/hubspot_connector): Facilitates communication with HubSpot, enabling seamless data integration and CRM functionality.

**AWS DynamoDB Integration**

- [**datawald_dynamodbagency**](https://github.com/ideabosque/datawald_dynamodbagency): Tailors and processes data with business-specific logic for DynamoDB, supporting database interactions.
- [**dynamodb_connector**](https://github.com/ideabosque/datawald_connector): Connects with AWS DynamoDB to execute efficient data transactions within the framework.

**AWS SQS Integration**

- [**datawald_sqsagency**](https://github.com/ideabosque/datawald_sqsagency): Processes messages from AWS SQS, embedding business rules to handle message flow effectively.
- [**sqs_connector**](https://github.com/ideabosque/sqs_connector): Manages connections with AWS SQS to enable message handling and integration within the framework.

**AWS S3 Integration**

- [**datawald_s3agency**](https://github.com/ideabosque/datawald_s3agency): Applies business logic to process and manage data for storage and retrieval in AWS S3.
- [**s3_connector**](https://github.com/ideabosque/s3_connector): Connects with AWS S3 to facilitate file management and data storage operations within the DataWald ecosystem.

## Installation and Configuration

### Step 1: Clone Repositories

1. Create a main project directory named `silvaengine`.
2. Within this folder, clone the following repositories:
    - [silvaengine_aws](https://github.com/ideabosque/silvaengine_aws)
    - [datawald_deployment](https://github.com/ideabosque/datawald_deployment)

### Step 2: Download and Set Up Docker

1. Clone the [silvaengine_docker](https://github.com/ideabosque/silvaengine_docker) project.
2. Create two directories named `logs` and `projects` inside the `www` directory at the root of the Docker Compose setup. Use the commands below:
    
    ```bash
    $ mkdir www/logs
    $ mkdir www/projects
    ```
    
3. Place your SSH private and public key files in the `python/.ssh` directory.
4. Set up a `.env` file in the root directory, using the provided `.env.example` for reference. Here’s a sample configuration:
    
    ```bash
    PIP_INDEX_URL=https://pypi.org/simple/ # Or use <https://mirrors.aliyun.com/pypi/simple/> for users in China
    PROJECTS_FOLDER={path to your projects directory}
    PYTHON=python3.11 # Python version
    DEBUGPY=/var/www/projects/silvaengine_aws/deployment/cloudformation_stack.py # Debug Python file path
    ```
    
    **Example Configuration:**
    
    - `PIP_INDEX_URL`: https://pypi.org/simple/
    - `PROJECTS_FOLDER`: "C:/Users/developer/GitHubRepos/silvaengine"
    - `DEBUGPY`: /var/www/projects/silvaengine_aws/deployment/cloudformation_stack.py
5. Build the Docker image:
    
    ```bash
    $ docker compose build
    ```
    
6. Start the Docker container:
    
    ```bash
    $ docker compose up -d
    ```
    

### Step 3: Setup and Deployment

1. **Create an S3 Bucket**: Ensure versioning is enabled (e.g., `xyz-silvaengine-aws`).
2. **Configure the `.env` File**: Place this file inside the `datawald_deployment` folder with the following settings:
    
    ```bash
    #### Stack Deployment Settings
    root_path=../silvaengine_aws # Root path of the stack
    site_packages=/var/python3.11/silvaengine/env/lib/python3.11/site-packages # Python packages path
    
    #### CloudFormation Settings
    bucket=silvaengine-aws # S3 bucket for zip packages
    region_name=us-west-2 # AWS region
    aws_access_key_id=XXXXXXXXXXXXXXXXXXX # AWS Access Key ID
    aws_secret_access_key=XXXXXXXXXXXXXXXXXXX # AWS Secret Access Key
    
    # AWS Lambda Function Variables
    REGIONNAME=us-west-2 # AWS region for resources
    EFSMOUNTPOINT=/mnt # EFS mount point (optional)
    PYTHONPACKAGESPATH=pypackages # Folder for large packages (optional)
    runtime=python3.11 # Lambda function runtime (optional)
    security_group_ids=sg-XXXXXXXXXXXXXXXXXXX # Security group IDs (optional)
    subnet_ids=subnet-XXXXXXXXXXXXXXXXXXX,subnet-XXXXXXXXXXXXXXXXXXX # Subnet IDs (optional)
    efs_access_point=fsap-XXXXXXXXXXXXXXXXXXX # EFS access point (optional)
    efs_local_mount_path=/mnt/pypackages # EFS local mount path (optional)
    {function name or layer name}_version=XXXXXXXXXXXXXXXXXXX # Function or layer version (optional)
    ```
    
    **Example Configuration:**
    
    ```bash
    #### Stack Deployment Settings
    root_path=../silvaengine_aws
    site_packages=/var/python3.11/silvaengine/env/lib/python3.11/site-packages
    
    #### CloudFormation Settings
    bucket=xyz-silvaengine-aws
    region_name=us-west-2
    aws_access_key_id=XXXXXXXXXXXXXXXXXXX
    aws_secret_access_key=XXXXXXXXXXXXXXXXXXX
    REGIONNAME=us-west-2
    runtime=python3.11
    ```
    

### Step 4: Deploy SilvaEngine Base

1. Run the following command to access the container:
    
    ```bash
    $ docker exec -it container-aws-suites-311 /bin/bash
    ```
    
2. Activate the virtual environment:
    
    ```bash
    source /var/python3.11/silvaengine/env/bin/activate
    ```
    
3. Navigate to the deployment directory and execute the CloudFormation stack:
    
    ```bash
    cd ./datawald_deployment
    python cloudformation_stack.py .env silvaengine
    ```

### Step 5: Deploy DataWald Integration Framework

1. Add entries into the `se-endpoints` (DynamoDB Table) collection, using the `endpoint_id` from the `lambda_config.json` file located in the `datawald_deployment` directory. The format for each entry should be as follows:
    
    ```json
    {
        "endpoint_id": {endpoint_id},
        "code": 0,
        "special_connection": true
    }
    ```
    
2. For each `endpoint_id` in the `lambda_config.json` file within `datawald_deployment`, insert two separate records into `se-connections` (DynamoDB table):
    - One record using the static `api_key` value '#####':
        
        ```json
        {
            "endpoint_id": {endpoint_id},
            "api_key": "#####",
            "functions": []
        }
        ```
        
    - Another record with the actual `api_key` associated with the deployed AWS API Gateway:
        
        ```json
        {
            "endpoint_id": {endpoint_id},
            "api_key": {api_key},
            "functions": []
        }
        ```
        
3. To access the container, execute the following command:
    
    ```bash
    $ docker exec -it container-aws-suites-311 /bin/bash
    ```
    
4. Activate the Python virtual environment by running:
    
    ```bash
    source /var/python3.11/silvaengine/env/bin/activate
    ```
    
5. Navigate to the `datawald_deployment` directory and execute the CloudFormation stack setup script:
    
    ```bash
    cd ./datawald_deployment
    sh dw_requirements.sh
    ```

### Step 6: Configuration

1. Initial Configuration Setup for the Foundation. To establish the base configuration, insert the following records into the `se-configdata` DynamoDB table:
    
    ```json
    {
      "setting_id": "datawald_agency",
      "variable": "DW_API_KEY",
      "value": "XXXXXXXXXXXXXXXXXXX"
    },
    {
      "setting_id": "datawald_agency",
      "variable": "DW_API_URL",
      "value": "<https://xxxxxxxxxx.execute-api.us-xxxxx-x.amazonaws.com/beta>"
    },
    {
      "setting_id": "datawald_agency",
      "variable": "DW_AREA",
      "value": "core"
    },
    {
      "setting_id": "datawald_agency",
      "variable": "DW_ENDPOINT_ID",
      "value": "dw"
    },
    {
      "setting_id": "datawald_agency",
      "variable": "input_queue_name",
      "value": "datawald_input_queue.fifo"
    },
    {
      "setting_id": "datawald_agency",
      "variable": "task_queue_name",
      "value": "silvaengine_task_queue.fifo"
    },
    {
      "setting_id": "datawald_agency",
      "variable": "tx_type",
      "value": {
        "asset": [
          "product",
          "inventory",
          "inventorylot",
          "pricelevel",
          "inventory_data"
        ],
        "person": [
          "customer",
          "vendor",
          "company",
          "contact",
          "company_type",
          "factory"
        ],
        "transaction": [
          "order",
          "invoice",
          "purchaseorder",
          "itemreceipt",
          "itemfulfillment",
          "opportunity",
          "quote",
          "rma",
          "billcredit",
          "payment",
          "inventoryadjustment",
          "creditmemo",
          "inventorytransfer"
        ]
      }
    }
    
    ```
    
    **Configuration Details:**
    
    - **DW_API_KEY**: The API key generated by the SilvaEngine base setup, used for authentication.
    - **DW_API_URL**: The API URL provided by the SilvaEngine base setup, serving as the endpoint for requests.
    - **DW_AREA**: Defines the area variable used by the function of the core module `datawald_interface_engine` within the `se-functions` DynamoDB table.
    - **DW_ENDPOINT_ID**: Identifies the endpoint for the core module, `datawald_interface_engine`.
    - **input_queue_name**: Specifies the SQS queue configured for `SQSAgency` and `SQSConnector` to receive incoming messages.
    - **task_queue_name**: Indicates the SQS queue used in SilvaEngine to dispatch tasks for asynchronous operations.
    - **tx_type**: Enumerates the supported data types for integration, categorized into assets, persons, and transactions.
2. Configure the Core Module `datawald_interface_engine`. Insert the following records into the `se-configdata` DynamoDB table:
    
    ```json
    {
      "setting_id": "datawald_interface_engine",
      "variable": "default_cut_date",
      "value": "2024-05-24T02:21:00+00:00"
    },
    {
      "setting_id": "datawald_interface_engine",
      "variable": "input_queue_name",
      "value": "datawald_input_queue.fifo"
    },
    {
      "setting_id": "datawald_interface_engine",
      "variable": "max_entities_in_message_body",
      "value": "200"
    },
    {
      "setting_id": "datawald_interface_engine",
      "variable": "sync_task_notification",
      "value": {
        "<endpoint_id>": {
          "<data_type>": "<async_function>"
        }
      }
    },
    {
      "setting_id": "datawald_interface_engine",
      "variable": "task_queue_name",
      "value": "silvaengine_task_queue.fifo"
    }
    ```
    
    **Configuration Details:**
    
    - **default_cut_date**: The default cut-off date for data synchronization.
    - **input_queue_name**: Specifies the SQS queue designated for `SQSAgency` and `SQSConnector` to receive incoming messages.
    - **max_entities_in_message_body**: Defines the maximum number of entities allowed in the message body when sending data via `task_queue`.
    - **sync_task_notification**: Configures notifications to trigger an asynchronous function based on `endpoint_id` and `data_type` when a synchronization task is completed or fails.
    - **task_queue_name**: Specifies the SQS queue used by SilvaEngine for dispatching tasks in asynchronous workflows.

3. Module Configuration for Each Application
    1. NSAgency for NetSuite Integration: NSAgency facilitates seamless data exchange with NetSuite, automating synchronization for enhanced operational efficiency. For setup details, see the [DataWald NSAgency GitHub repository](https://github.com/ideabosque/datawald_nsagency).