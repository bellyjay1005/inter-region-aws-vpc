import os
import sys
import boto3
import yaml
import botocore
import traceback
from boto3.session import Session

# Define global variables
CONFIGS=sys.argv[1]
TEMPLATES=sys.argv[2]
# TEMP='file:///home/ec2-user/environment/jelili.adebello-newhire-training/jelili-newhire-dry-s3-template.yaml'
# TEMPLATE_BODY='file://${DIR}/${TEMP}'

print('Loading function')


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

def build_template_path(template_dir):
   """
        Read stack template directory that contains all templates
        
        Args:
            template_dir: directory containing template files to be read
        Returns:
            The template file path     
   """
   # templates = os.listdir(template_dir)
   # for template in templates:
   #    if template.endswith('.yaml'):
   #       return template
   template_path = '/Users/jeliliadebello/Documents/multi-vpc-test/'+template_dir
   return template_path

def build_stack_parameters(config):
   """
      Read input configuration file that contains stack creation arguments and parameters to create stack
        
        Args:
            config: dictionary containing parameter values to be read
        Returns:
            List of Parameters for cloudformation template    
   """
   params_list = []
   for k, v in config.iteritems():
      params = {}
      params['ParameterKey'] = k
      params['ParameterValue'] = v
      params_list.append(params)

   return params_list

def regional_client(config):
   """
      Read input configuration file that contains stack creation arguments and parameters
      and read Region parameter to define regional client to create stack

      Args:
         config: loaded yaml file to be read
      Returns:
         The low-level client representing AWS CloudFormation
      Raises:
         Exception: If no matching region is found or client could not be extracted from yaml file
     
   """
   try:
      # get the loaded yaml file and extract "Region" parameter to define cloudformation client
      region = config['Region']
      cfn = boto3.client('cloudformation', region_name=region)
      return cfn
   except botocore.exceptions.ClientError as e:
      return e

class vpc_deployment_manager(object):
   def __init__(self, config):
      self.cfn = regional_client(config)

   def stack_exists(self, stack):
      """
         Check if a stack exists or not

         Args:
            stack: The stack to check

         Returns:
            True or False depending on whether the stack exists

         Raises:
            Any exceptions raised .describe_stacks() besides that
            the stack doesn't exist.

      """
      try:
         self.cfn.describe_stacks(StackName=stack)
         return True
      except botocore.exceptions.ClientError as e:
         if "does not exist" in e.response['Error']['Message']:
            return False
         else:
            raise e

   def get_stack_status(self, stack):
      """
         Get the status of an existing CloudFormation stack

         Args:
            stack: The name of the stack to check

         Returns:
            The CloudFormation status string of the stack such as CREATE_COMPLETE

         Raises:
            Exception: Any exception thrown by .describe_stacks()

      """
      stack_description = self.cfn.describe_stacks(StackName=stack)
      return stack_description['Stacks'][0]['StackStatus']

   def create_stack(self, stack, template, parameters):
      """
         Starts a new CloudFormation stack creation

         Args:
            stack: The stack to be created
            template: The template for the stack to be created with

         Throws:
            Exception: Any exception thrown by .create_stack()
      """
      self.cfn.create_stack(StackName=stack, TemplateBody=template, Parameters=parameters)
      waiter = self.cfn.get_waiter('stack_create_complete')
      waiter.wait(StackName=stack)

   def update_stack(self, stack, template, parameters):
      """Start a CloudFormation stack update

         Args:
            stack: The stack to update
            template: The template to apply

         Returns:
            True if an update was started, false if there were no changes
            to the template since the last update.

         Raises:
            Exception: Any exception besides "No updates are to be performed."

      """
      try:
         self.cfn.update_stack(StackName=stack, TemplateBody=template, Parameters=parameters)
         waiter = self.cfn.get_waiter('stack_update_complete')
         waiter.wait(StackName=stack)
         return True

      except botocore.exceptions.ClientError as e:
         if e.response['Error']['Message'] == 'No updates are to be performed.':
            return False
         else:
            raise Exception('Error updating CloudFormation stack "{0}"'.format(stack), e)

   def create_or_update_vpc_stack(self, stack, template, parameters):
      """
         Starts the stack creation or update process

         If the stack exists then update, otherwise create.

         Args:
            stack_name: The name of stack to create or update
            template: The template to create or update the stack with

      """
      if self.stack_exists(stack):
         status = self.get_stack_status(stack)
         if status not in ['CREATE_COMPLETE', 'ROLLBACK_COMPLETE', 'UPDATE_COMPLETE']:
            # If the CloudFormation stack is not in a state where
            # it can be updated again then fail the job right away.
            print('Stack cannot be updated when status is: ' + status)
            return

         resource_updates = self.update_stack(stack, template, parameters)

         if resource_updates:
            # If there were updates then continue and succeed with progress of the update.
            print('Stack update started....')  

         else:
            # If there were no updates then succeed the job immediately 
            print('There were no stack updates')    
      else:
         # If the stack doesn't already exist then create it instead of updating it.
         self.create_stack(stack, template, parameters)
         # Continue the job so the pipeline will wait for the CloudFormation stack to be created.
         print('Stack creation started....')   

def main():
      setup_data = load_yaml_file(CONFIGS)
      print('Listing configuration to setup VPC in specified regions.......')

      try:
         for single_setup_data in setup_data:

            # Extract region to deploy stack
            vpc_region = single_setup_data['Region']
            print('Region to deploy vpc = ' + vpc_region)

            # Extract the vpc name and region and create a stack name
            vpc_name = single_setup_data['vpc_name']
            stack_name = vpc_region+'-'+vpc_name
            print ('Stack name for deployed vpc = ' + stack_name)

            # Extract the template file to create stack
            working_dir = TEMPLATES
            template_file = single_setup_data['Template_file']
            template = working_dir+template_file
            with open(template,'r') as s:
               template_body = s.read()
            print ('Template file used to deploy vpc = ' + template)

            # Extract the input parameters to create or update stack
            parameter_values=build_stack_parameters(single_setup_data['Parameters'])
            print('Parameter key-value for vpc stack = ' + str(parameter_values))

            # Deploy Stack
            stacks = vpc_deployment_manager(single_setup_data)
            stacks.create_or_update_vpc_stack(stack_name, template_body, parameter_values)
            print('provisioning inter-Region multi-vpc netwrok environment.......')


      except Exception as e:
         # If any other exceptions which we didn't expect are raised
         # then fail the job and log the exception message.
         print('Function failed due to exception.')
         print(e)
         traceback.print_exc()
         print('Function exception: ' + str(e))

      print('VPC deployment complete.')
      return "Complete."

if __name__ =="__main__":
   main()























