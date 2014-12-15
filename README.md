sch-vulnpryer-orchestration
===========================


High level description of what the script does:
  - Prepares the IAM roles. Sets their permission and trust policies which are defined under iam_policies folder
  - Drops and rebuilds the Opsworks stack
  - Prepares the custom monitoring script and uploads to S3
  - Drops and rebuilds the Data Pipeline

Prerequisites:

  - Github repo for custom recipes
  - SNS Topic ARN used for notification
  - S3 bucket/path created where custom scripts will be stored
  - S3 bucket/path created where DataPipeline will store logs
  - Persistent EBS volume for mongodb store 
  - Node with Python boto installed (>=v2.33.0)

Instructions:

In a node with Python boto installed (>=v2.33.0):
1. Download the code

         git clone https://github.com/cascadeo/sch-vulnpryer-orchestration

2. Create an IAM user for Vulnpryer. The Data Pipeline objects will be owned by this user. Pipelines aren't visible to other IAM users in the account so a generic IAM user should be used for management. Reference:  https://forums.aws.amazon.com/thread.jspa?threadID=138201.

3. Configure IAM User.
         - Generate access keys
         - Set its permission policy to iam_policies/iam_user_policy (https://github.com/cascadeo/sch-vulnpryer-orchestration/blob/master/iam_policies/iam_user_policy)

Note: If you wish your own IAM user account to own the stack and pipeline, then ensure your IAM account has the required policies indicated above. 

4. Populate deploy_vulnpryer.cfg configuration file with desired values. Descriptions are placed above the parameters as comments.

5. Run the script

         python deploy_vulnpryer.py
Sample successful run:

	$ python deploy_vulnpryer.py
	------------------------------
	Preparing Vulnpryer IAM Roles
	------------------------------
	Updating assume role policy of DataPipelineVulnpryerRole
	Updating attached permission policies of DataPipelineVulnpryerRole
	Updating role and instance profile association of DataPipelineVulnpryerRole
	Updating assume role policy of DataPipelineVulnpryerResourceRole
	Updating attached permission policies of DataPipelineVulnpryerResourceRole
	Updating role and instance profile association of DataPipelineVulnpryerResourceRole
	Updating assume role policy of OpsworksVulnpryerRole
	Updating attached permission policies of OpsworksVulnpryerRole
	Updating role and instance profile association of OpsworksVulnpryerRole
	Updating assume role policy of OpsworksVulnpryerResourceRole
	Updating attached permission policies of OpsworksVulnpryerResourceRole
	Updating role and instance profile association of OpsworksVulnpryerResourceRole
	Successfully prepared IAM roles
	------------------------------------
	Building Vulnpryer Opsworks Stack
	------------------------------------
	Stack sch-vulnpryer-qa-stack exists. Deleting stack with Stack ID 0c82b343-cfd9-4882-a583-f99934254a0f
	Successfully built Opsworks Stack sch-vulnpryer-qa-stack with stack id 1ca5ce52-7891-41ff-89ef-f325ac54a7e4
	------------------------------------
	Preparing Vulnpryer Custom Script
	------------------------------------
	Plugged in region us-east-1 and opsworks instance id ef988056-a283-4fe0-8f68-7158710a2fda
	Uploaded script <Key: roy-testbucket,sch-scripts/start_vulnpryer.py>
	------------------------------------
	Building Vulnpryer Data Pipeline
	------------------------------------
	Pipeline testroy35 with ID df-0658003JI709EL10CMS created on us-east-1
	Pipeline objects created
	Successfully built pipeline

6. Log into AWS as the IAM user owner to the AWS Data Pipeline console on the specified region.

7. Activate to run the pipeline.

