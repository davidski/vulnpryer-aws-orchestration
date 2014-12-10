sch-vulnpryer-orchestration
===========================

Instructions:

1. Create an IAM user for Vulnpryer. The Opsworks stack and Data Pipeline objects will be owned by this user. Pipelines aren't visible to other IAM users in the account so a generic IAM user should be used for management.

https://forums.aws.amazon.com/thread.jspa?threadID=138201

2. Generate Access keys for the IAM User

3. Python Boto at least v2.33.0 is needed to run. One can use the latest Amazon AMI Linux provided by AWS.

4. Download the code
 
	git clone https://github.com/roy-cascadeo/sch-vulnpryer-orchestration.git

5. Populate configuration file deploy_vulnpryer.cfg with correct values
	a. General Settings section
		- access keys of the created IAM user
                - aws region - all objects are expected to be created under this region
        b. Opsworks Settings section
                - opworks IAM roles
                    opsworks_role - used by service 
                    opsworks_resource_role - the instance profile used by the instances launched by the service
                - Set the volume id and API keys in custom_json
                - Define git repository on custom_cookbook_source
                - and other parameters corresponding to various Opsworks stack settings.

         c. Custom Script Settings section - the s3 bucket and path to upload the custom script. Bucket is expected to be in the same region .

         d. Data Pipeline Settings section
                 - Data Pipelien IAM roles
                    pipeline_role - used by service 
                    pipeline_resource_role - the instance profile used by the instances launched by the service 

		- Each Pipeline object is represented by a parameter with dictionary definitions. Update the fields to desired values

6. Run the script
  
       python deploy_vulnpryer.py

   High Level on What the script does
       - Prepares the IAM roles. Sets their permission and trust policies which are defined under iam_policies folder 
       - Drops and rebuilds the Opsworks stack
       - Prepares the custom monitoring script and upload to S3
       - Drops and rebuilds the Data Pipeline

7. Log on as your IAM USer to the AWS Data Pipeline console on the specified region. You might want to change the scheduled start date to a recent date to address warning before Activating.

8. Activate to run the Pipeline
