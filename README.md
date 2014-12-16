sch-vulnpryer-orchestration
===========================


High-level Description
----------------------
  - Prepares the IAM roles. Sets their permission and trust policies which are defined under iam_policies folder
  - Drops and rebuilds the Opsworks stack
  - Prepares the custom monitoring script and uploads to S3
  - Drops and rebuilds the Data Pipeline

Prerequisites
--------------
  - Github repo for custom recipes
  - SNS Topic ARN used for notification
  - S3 bucket/path created where custom scripts will be stored
  - S3 bucket/path created where DataPipeline will store logs
  - Persistent EBS volume for mongodb store 
  - Node with Python boto installed (>=v2.33.0)

Usage
-----
In a node with Python boto installed (>=v2.33.0):

1. Download the code.

         git clone https://github.com/cascadeo/sch-vulnpryer-orchestration

2. Create an IAM user for Vulnpryer. The Data Pipeline objects will be owned by this user. Pipelines aren't visible to other IAM users in the account so a generic IAM user should be used for management. Reference:  https://forums.aws.amazon.com/thread.jspa?threadID=138201.

3. Configure IAM user and perform the following:
	- Generate access keys
	- Set its permission policy to iam_policies/iam_user_policy (https://github.com/cascadeo/sch-vulnpryer-orchestration/blob/master/iam_policies/iam_user_policy)

	Note: If you wish your own IAM user account to own the stack and pipeline, then ensure your IAM account has the required policies indicated above. 

4. Populate deploy_vulnpryer.cfg configuration file with desired values. Descriptions are placed above the parameters as comments.

5. Run the script

         python deploy_vulnpryer.py

6. Log into AWS as the IAM user owner to the AWS Data Pipeline console on the specified region.

7. Activate to run the pipeline.

