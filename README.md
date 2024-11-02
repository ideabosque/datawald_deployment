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