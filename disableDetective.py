#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" python3 disableDetective.py --master_account 555555555555 --assume_role detectiveAdmin --disabled_regions us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1 --input_file accounts.csv
"""
__author__ = "Ryan Nolette"
__copyright__ = "Amazon 2020"
__credits__ = ["Ryan Nolette",
               "https://github.com/sonofagl1tch"]
__license__ = "Apache"
__version__ = "1.0.1"
__maintainer__ = "Ryan Nolette"
__email__ = "detective-demo-requests@amazon.com"
__status__ = "Production"

import argparse
import itertools
import logging
import re
import sys
import typing
import boto3
import botocore.exceptions

FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format=FORMAT)


def setup_command_line(args = None) -> argparse.Namespace:
    """
    Configures and reads command line arguments.

    Returns:
        An argparse.Namespace object containing parsed arguments.

    Raises:
        argpare.ArgumentTypeError if an invalid value is used for
        master_account argument.
    """
    def _master_account_type(val: str, pattern: str = r'[0-9]{12}'):
        if not re.match(pattern, val):
            raise argparse.ArgumentTypeError
        return val

    # Setup command line arguments
    parser = argparse.ArgumentParser(description=('Unlink AWS Accounts from a central '
                                                  'Detective Account, or delete the entire Detective graph.'))
    parser.add_argument('--master_account', type=_master_account_type,
                        required=True,
                        help="AccountId for Central AWS Account.")
    parser.add_argument('--input_file', type=argparse.FileType('r'),
                        help=('Path to CSV file containing the list of '
                              'account IDs and Email addresses. '
                              'This does not need to be provided if you use the delete_graph flag.'))
    parser.add_argument('--assume_role', type=str, required=True,
                        help="Role Name to assume in each account.")
    parser.add_argument('--delete_graph', action='store_true',
                        help=('Delete the master Detective graph. '
                              'If not provided, you must provide an input file.'))
    parser.add_argument('--disabled_regions', type=str,
                        help=('Regions to disable Detective. If not specified, '
                              'all available regions disabled.'))
    args = parser.parse_args(args)
    if not args.delete_graph and not args.input_file:
        raise parser.error("Either an input file or the delete_graph flag should be provided.")

    return args


def read_accounts_csv(input_file: typing.IO) -> typing.Dict:
    """
    Parses contents from the CSV file containing the accounts and email addreses.

    Args:
        input_file: A file object to read CSV data from.

    Returns:
        A dictionary where the key is account ID and value is email address.
    """
    account_re = re.compile(r'[0-9]{12}')
    aws_account_dict = {}

    if not input_file:
        return aws_account_dict

    for acct in input_file.readlines():
        split_line = acct.strip().split(',')

        if len(split_line) != 2:
            logging.exception(f'Unable to process line: {acct}.')
            continue

        account_number, email = split_line
        if not account_re.match(account_number):
            logging.error(
                f'Invalid account number {account_number}, skipping.')
            continue

        aws_account_dict[account_number.strip()] = email.strip()

    return aws_account_dict


def get_regions(session: boto3.Session, user_regions: str) -> typing.List[str]:
    """
    Get AWS regions to disable Detective from.

    Args:
        session: boto3 session.
        args_region: User specificied regions.

    Returns:
        A list of the region names to disable Detective from.
    """
    detective_regions = []
    if user_regions:
        detective_regions = user_regions.split(',')
        logging.info(
            f'disabling members in these regions: {detective_regions}')
    else:
        detective_regions = session.get_available_regions('detective')
        logging.info(
            f'disabling members in all available Detective regions {detective_regions}')
    return detective_regions


def assume_role(aws_account_number: str, role_name: str) -> boto3.Session:
    """
    Assumes the provided role in each account and returns a Detective client.

    Args:
        - aws_account_number: AWS Account Number
        - role_name: Role to assume in target account

    Returns:
        Detective client in the specified AWS Account and Region
    """
    try:
        # Beginning the assume role process for account
        sts_client = boto3.client('sts')

        # Get the current partition
        partition = sts_client.get_caller_identity()['Arn'].split(":")[1]

        response = sts_client.assume_role(
            RoleArn='arn:{}:iam::{}:role/{}'.format(
                partition,
                aws_account_number,
                role_name
            ),
            RoleSessionName='EnableDetective'
        )
        # Storing STS credentials
        session = boto3.Session(
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken']
        )
    except Exception as e:
        logging.exception(f'exception: {e}')

    logging.info(f"Assumed session for {aws_account_number}.")

    return session


def get_graphs(d_client: botocore.client.BaseClient) -> typing.List[str]:
    """
    Get graphs in a specified region.

    Args:
        - d_client: Detective boto3 client generated from the master session.

    Returns:
        List of graph Arns.
    """
    try:
        response = d_client.list_graphs()
    except botocore.exceptions.EndpointConnectionError:
        logging.exception(f'exception: {e}')
        return []

    # use .get function to avoid KeyErrors when a dictionary key doesn't exist
    # it returns an empty list instead.
    # map iterates over all elements under a list and applied a function to them,
    # in this specific case, the element 'Arn' is extracted from the dictionary
    # (graphlist is a list of dictionaries)
    return [x['Arn'] for x in response.get('GraphList', [])]


def get_members(d_client: botocore.client.BaseClient, graphs: typing.List[str]) ->\
        (typing.Dict[str, typing.Set[str]], typing.Dict[str, typing.Set[str]]):
    """
    Get member accounts for all behaviour graphs in a region.

    Args:
        - d_client: Detective boto3 client generated from the master session.
        - graphs: List of graphs arns

    Returns:
        Two dictionaries: one with all account ids, other with the ones pending to accept
        the invitation.
    """
    try:
        # itertools.tee creates two independent iterators from a single one. This way
        # we can iterate the iterator twice: one to return all elements and other to return
        # the ones pending to be invited.
        ####
        # check the value of NextToken in the response. if it is non-null, pass it back into a subsequent list_members call (and keep doing this until a null token is returned)
        def _master_memberList(g: str) -> typing.List[typing.Dict]:
            # create a list to append the member accounts
            memberAccounts = []
            # create a dictionary for the nextToken from each call
            tokenTracker = {}
            # loop through list_members call results and take action for each returned result
            while True:
                # list_members of graph "g" and return the first 100 results
                members = d_client.list_members(
                    GraphArn=g, MaxResults=100, **tokenTracker)
                # add the returned list members to the list
                memberAccounts.extend(members['MemberDetails'])
                # if the returned results have a "NextToken" key then use it to query again
                if 'NextToken' in members:
                    tokenTracker['NextToken'] = members['NextToken']
                # if the returned results do not have a "NextToken" key then exit the loop
                else:
                    break
            # return members list.
            # The return statement doesn't need ()
            return memberAccounts
    except Exception as e:
        logging.exception(f'exception when getting memebers: {e}')
    # iterate through each list and return results
    all_ac, pending = itertools.tee((g, _master_memberList(g))
                                    for g in graphs)
    return ({g: {x['AccountId'] for x in v} for g, v in all_ac},
            {g: {x['AccountId'] for x in v if x['Status'] == 'INVITED'} for g, v in pending})


def delete_members(d_client: botocore.client.BaseClient, graph_arn: str,
                   account_dict: typing.Dict[str, str]) -> typing.Set[str]:
    """
    delete member accounts for all accounts in the csv that are not present in the graph member set.

    Args:
        - d_client: Detective boto3 client generated from the master session.
        - graph_arn: Graph to add members to.
        - account_dict: Accounts read from the CSV input file.

    Returns:
        Set with the IDs of the successfully deleted accounts.
    """
    try:
        accountIDs = list(account_dict.keys())
        response = d_client.delete_members(GraphArn=graph_arn,
                                        AccountIds=accountIDs)
        for error in response['UnprocessedAccounts']:
            logging.exception(f'Could not delete member for account {error["AccountId"]} in '
                            f'graph {graph_arn}: {error["Reason"]}')
    except e:
        logging.error(f'error when deleting member: {e}')

def chunked(it, size):
    it = iter(it)
    while True:
        p = tuple(itertools.islice(it, size))
        if not p:
            break
        yield p

if __name__ == '__main__':
    args = setup_command_line()
    aws_account_dict = read_accounts_csv(args.input_file)

    # making sure that we either have an account list to delete from graphs or the delete_graph flag is provided.
    if len(list(aws_account_dict.keys())) == 0 and not args.delete_graph:
        logging.error("The delete_graph flag was False while the provided account list is empty. "\
            "Please check your inputs and re-run the script.")
        exit(1)

    try:
        session = boto3.session.Session()
        detective_regions = get_regions(session, args.disabled_regions)
        master_session = assume_role(args.master_account, args.assume_role)
    except NameError as e:
        # logging.exception prints the full traceback, logging.error just prints the error message.
        # In this case, the NameError is handled in a specific way: it is an expected exception
        # and the traceback doesn't add any value to the error message.
        logging.error(f'Master account is not defined: {e.args}')
    except Exception as e:
        # in this case, there has been an unhandled exception, something that wasn't estimated.
        # Having the error traceback helps us know what happened and help us find a solution
        # for the bug. The code should never arrive to this except clause, but if it does
        # we want as much information as possible and that's why we use logging.traceback.
        # In this case the traceback adds LOTS of value.
        logging.exception(f'error creating session {e.args}')

    #Chunk the list of accounts in the .csv into batches of 50 due to the API limitation of 50 accounts per invokation
    for chunk in chunked(aws_account_dict.items(), 50):

        for region in detective_regions:
            try:
                d_client = master_session.client('detective', region_name=region)
                graphs = get_graphs(d_client)
                if not graphs:
                    logging.info(f'Amazon Detective has already been disabled in {region}')
                else:
                    logging.info(f'Disabling Amazon Detective in region {region}')

                try:
                    for graph in graphs:
                        if not args.delete_graph:
                            delete_members(d_client, graph, chunk)
                        else:
                            d_client.delete_graph(graph)
                except NameError as e:
                    logging.error(f'account is not defined: {e}')
                except Exception as e:
                    logging.exception(f'{e}')

            except NameError as e:
                logging.error(f'account is not defined: {e}')
            except Exception as e:
                logging.exception(f'error with region {region}: {e}')
