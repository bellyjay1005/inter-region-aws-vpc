import os
import sys
import boto3
import yaml
import botocore

# from boto3.session import Session

# Define global variables
CONFIGS=sys.argv[1]


print('Loading function')

# cfn = boto3.client('cloudformation')

# class 

def load_yaml_file(yaml_file):
   """
     Read input configuration file that contains stack creation arguments and parameters
     
     Args:
         yaml_file: .yaml file to be read
     Returns:
         The input dictionary found returned as a list
     Raises:
         Exception: If no matching artifact is found
     
   """
   try:
     # Get the configuration parameters which contain the region, vpc name, template filename, VPC CIDR blocks
     s = open(yaml_file).read()
     config = list(yaml.load_all(s))[0]

   except Exception as e:
     # We're expecting the user parameters to be encoded as YAML
     # so we can pass multiple values. If the YAML can't be decoded
     # then return failure with a helpful message.
     print(e)
     raise Exception('Input configuration parameters could not be decoded as YAML')

   return config

# def create_single_vpc_config(param):
#    """
#      Parse the loaded yaml file for each vpc configurations setup to create a single vpc stack
     
#      Args:
#          param: loaded yaml file with user defined setup to create all vpc
#      Returns:
#          A single dictionary of configuration setup for individual vpc to be built
#      Raises:
#          Exception: If no matching artifact is found
     
#    """
#    try:
#       # Get the loaded configuration and breakdown into individual vpc input parameters
#       single_param = a

# def deploy_or_update_vpc_stack(self, stack_name, template):
#    """
#       Starts the stack creation or update process

#       If the stack exists then update, otherwise create.

#       Args:
#         stack_name: The name of stack to create or update
#         template: The template to create or update the stack with

#    """
#    if stack_exists(stack):
#      status = get_stack_status(stack)
#      if status not in ['CREATE_COMPLETE', 'ROLLBACK_COMPLETE', 'UPDATE_COMPLETE']:
#          # If the CloudFormation stack is not in a state where
#          # it can be updated again then fail the job right away.
#          put_job_failure(job_id, 'Stack cannot be updated when status is: ' + status)
#          return
     
#      were_updates = update_stack(stack, template)
     
#      if were_updates:
#          # If there were updates then continue the job so it can monitor
#          # the progress of the update.
#          continue_job_later(job_id, 'Stack update started')  
         
#      else:
#          # If there were no updates then succeed the job immediately 
#          put_job_success(job_id, 'There were no stack updates')    
#    else:
#      # If the stack doesn't already exist then create it instead
#      # of updating it.
#      create_stack(stack, template)
#      # Continue the job so the pipeline will wait for the CloudFormation
#      # stack to be created.
#      continue_job_later(job_id, 'Stack create started')   

def main():
      setup_data = load_yaml_file(CONFIGS)
      print('This is a list of configuration to setup VPC in specified regions.......')
      print(setup_data)

if __name__ == "__main__": 
      main()























