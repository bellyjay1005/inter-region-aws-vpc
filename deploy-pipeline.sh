#!bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

# GLOBAL VARIABLES
REGION="us-west-2"
PIPELINE_STACKNAME="vpc-pipeline"
PIPELINE_PARAMETERS="pipeline-parameters.json"
TEMPLATE="vpc-pipeline.yaml"
GITHUB_WEBHOOK_NAME="jelili-week7-GitHub-Webhook"

PARAM_BODY=file://${DIR}/${PIPELINE_PARAMETERS}
TEMP_BODY=file://${DIR}/${TEMPLATE}


###########################################
# DEPLOY PIPELINE USING AWS CODEPIPELINE  #
###########################################
        
# Get Secret Parameter for GitHub Personal Access Token from SSM 
GIT_WEBHOOK_TOKEN="$(aws ssm get-parameter \
                --name ${GITHUB_WEBHOOK_NAME} \
                --with-decryption \
                --query 'Parameter.[Value]' \
                --output text \
                --region ${REGION})"

# Update pipeline parameters with GitHub WebHook Token
sed -i "s/GIT_WEBHOOK_TOKEN_VALUE/$GIT_WEBHOOK_TOKEN/g" ${PIPELINE_PARAMETERS}

# Create CodePipeline Pipeline to deploy pipeline
aws cloudformation update-stack \
    --stack-name ${PIPELINE_STACKNAME} \
    --template-body ${TEMP_BODY} \
    --parameters ${PARAM_BODY} \
    --capabilities CAPABILITY_NAMED_IAM \
    --region ${REGION}
    
# Wait for stack creation condition to be satisfied before returning values
aws cloudformation wait \
  stack-update-complete \
  --region ${REGION} \
  --stack-name ${PIPELINE_STACKNAME}
