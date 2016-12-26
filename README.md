VulnPryer-AWS-Ochestration
===========================


High-level Description
----------------------
  - Prepares the IAM roles; sets their permission and trust policies which are defined in the iam_policies folder
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

         git clone https://github.com/davidski/vulnpryer-aws-orchestration

2. Create an IAM user for Vulnpryer. The Data Pipeline objects will be owned by this user. Pipelines aren't visible to other IAM users in the account so it is suggested a generic IAM user be used for management. Reference:  https://forums.aws.amazon.com/thread.jspa?threadID=138201.

3. Configure IAM user and perform the following:
	- Generate access keys
	- Set its permission policy to [iam_policies/iam_user_policy](iam_policies/iam_user_policy)

	Note: If you wish your own IAM user account to own the stack and pipeline, then ensure your IAM account has the required policies indicated above. 

4. Populate deploy_vulnpryer.cfg configuration file with desired values. Descriptions are placed above the parameters as comments.

5. Run the script

         python deploy_vulnpryer.py

6. Log into the AWS Data Pipeline console as the IAM user that owns the pipeline, in the specified region.

7. Activate to run the pipeline.

