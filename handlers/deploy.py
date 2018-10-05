import os
import sys
import boto3
from yaml import load, dump
import botocore

# from boto3.session import Session

# Define global variables
CONFIGS=sys.argv[1]


print('Loading function')

# cfn = boto3.client('cloudformation')

# class 

def load_configs(yaml_file):
    """
	    Read input configuration file that contains stack creation arguments and parameters
	    
	    Args:
	        setup: .yaml file to be read
	    Returns:
	        The input dictionary found
	    Raises:
	        Exception: If no matching artifact is found
	    
    """
    try:
        # Get the configuration parameters which contain the region, vpc name, template filename, VPC CIDR blocks
	    config = yaml.load(file(yaml_file, 'r'))

    except Exception as e:
        # We're expecting the user parameters to be encoded as YAML
        # so we can pass multiple values. If the YAML can't be decoded
        # then return failure with a helpful message.
        print(e)
        raise Exception('Input configuration parameters could not be decoded as YAML')

    return config

def main():
        setup_data = load_configs(CONFIGS)
        print('This is a list of configuration to setup VPC in specified regions.......')
        print(setup_data)

if __name__ == "__main__": 
    main()