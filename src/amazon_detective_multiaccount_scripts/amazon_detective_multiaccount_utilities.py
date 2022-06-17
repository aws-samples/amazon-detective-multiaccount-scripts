#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Amazon Detective"
__copyright__ = "Amazon 2020"
__credits__ = "Amazon Detective"
__license__ = "Apache"
__version__ = "1.1.0"
__maintainer__ = "Amazon Detective"
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
                f'Invalid account number {account_number}, skipping. Account number should be 12 digits long and should contain only digits.')
            continue

        aws_account_dict[account_number.strip()] = email.strip()

    return aws_account_dict


def get_regions(session: boto3.Session, skip_prompt: bool, user_regions=None) -> typing.List[str]:
    """
    Get AWS regions to disable/enable Detective from.

    Args:
        session: boto3 session.
        skip_prompt: Customer agree to skip the prompt and agree to make the change
        user_regions: User specified regions. (Optional)

    Returns:
        A list of the region names to disable/enable Detective from, otherwise None.
    """
    # Initialize the confirm variable
    confirm = 'N'
    if user_regions:
        detective_regions = user_regions.split(',')
        logging.info(
            f'Modifying members in these regions: {detective_regions}')
    else:
        if not skip_prompt:
            confirm = input('Should Amazon Detective be enabled/disabled in all regions: {}? Enter [Y/N]: '
                            .format(session.get_available_regions('detective')))
        if skip_prompt or confirm == 'Y' or confirm == 'y':
            detective_regions = session.get_available_regions('detective')
            logging.info(
                f'Modifying members in all available Detective regions {detective_regions}')
        else:
            logging.info(
                f'Modification will not be made in this execution,'
                f'please specify regions in command line arguments')
            return None
    return detective_regions


def assume_role(aws_account_number: str, role_name: str, role_session_name: str) -> boto3.Session:
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
            RoleSessionName=role_session_name
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
        - d_client: Detective boto3 client generated from the admin session.

    Returns:
        List of graph Arns.
    """
    try:
        response = d_client.list_graphs()
    except botocore.exceptions.EndpointConnectionError as e:
        logging.exception(f'exception: {e}')
        return []

    # use .get function to avoid KeyErrors when a dictionary key doesn't exist
    # it returns an empty list instead.
    # map iterates over all elements under a list and applied a function to them,
    # in this specific case, the element 'Arn' is extracted from the dictionary
    # (graphlist is a list of dictionaries)
    return [x['Arn'] for x in response.get('GraphList', [])]


def get_members(d_client: botocore.client.BaseClient, graphs: typing.List[str]) -> \
        (typing.Dict[str, typing.Set[str]], typing.Dict[str, typing.Set[str]], typing.Dict[str, typing.Set[str]]):
    """
    Get member accounts for all behaviour graphs in a region.

    Args:
        - d_client: Detective boto3 client generated from the admin session.
        - graphs: List of graphs arns

    Returns:
        Two dictionaries: one with all account ids, other with the ones pending to accept
        the invitation.
    """

    # itertools.tee creates two independent iterators from a single one. This way
    # we can iterate the iterator twice: one to return all elements and other to return
    # the ones pending to be invited.
    ####
    # check the value of NextToken in the response. if it is non-null, pass it back into a subsequent list_members call (and keep doing this until a null token is returned)
    def _admin_member_list(g: str) -> typing.List[typing.Dict]:
        # create a list to append the member accounts
        member_accounts = []
        # create a dictionary for the nextToken from each call
        token_tracker = {}
        # loop through list_members call results and take action for each returned result
        while True:
            # list_members of graph "g" and return the first 100 results
            members = d_client.list_members(GraphArn=g, MaxResults=100, **token_tracker)
            # add the returned list members to the list
            member_accounts.extend(members['MemberDetails'])
            # if the returned results have a "NextToken" key then use it to query again
            if 'NextToken' in members:
                token_tracker['NextToken'] = members['NextToken']
            # if the returned results do not have a "NextToken" key then exit the loop
            else:
                break
        # return members list.
        # The return statement doesn't need ()
        return member_accounts

    # iterate through each list and return results
    try:
        all_ac, pending, verification_fail = itertools.tee(((g, _admin_member_list(g)) for g in graphs), 3)
    except Exception as e:
        logging.exception(f'exception when getting members: {e}')

    return ({g: {x['AccountId'] for x in v} for g, v in all_ac},
            {g: {x['AccountId'] for x in v if x['Status'] == 'INVITED'} for g, v in pending},
            {g: {x['AccountId'] for x in v if x['Status'] == 'VERIFICATION_FAILED'} for g, v in verification_fail})


def chunked(it, size):
    """
    Chunk iterable data according to specified size

    Args:
        - it: Iterable data
        - size: Specified chunk size
    Returns:
        p: tuple format data
    """
    it = iter(it)
    while True:
        p = tuple(itertools.islice(it, size))
        if not p:
            break
        yield p


def collect_session_and_regions(admin_account: str, role: str, regions: str, role_session_name: str, skip_prompt: bool) -> \
        (typing.List[str], boto3.Session):
    """
    Get detective_regions and admin_session variables.

    Args:
        - admin_account: AccountId for Central AWS Account.
        - role: Role Name to assume in each account.
        - regions: User specified regions or None
        - role_session_name: String that use in assume_role to indicate calling script
        - skip_prompt: Customer agree to skip the prompt and agree to make the change

    Returns:
        detective_regions: A list of the region names to disable/enable Detective from, otherwise None.
        admin_session: Detective client in the specified AWS Account and Region
    """
    try:
        session = boto3.session.Session()
        detective_regions = get_regions(session, skip_prompt, regions)
        admin_session = assume_role(admin_account, role, role_session_name)

        return detective_regions, admin_session

    except NameError as ex:
        # logging.exception prints the full traceback, logging.error just prints the error message.
        # In this case, the NameError is handled in a specific way: it is an expected exception
        # and the traceback doesn't add any value to the error message.
        logging.error(f'Admin account is not defined: {ex.args}')
    except Exception as e:
        # in this case, there has been an unhandled exception, something that wasn't estimated.
        # Having the error traceback helps us know what happened and help us find a solution
        # for the bug. The code should never arrive to this except clause, but if it does
        # we want as much information as possible and that's why we use logging.traceback.
        # In this case the traceback adds LOTS of value.
        logging.exception(f'error creating session {e.args}')


def check_region_existence_and_modify(args: argparse.Namespace, detective_regions: typing.List[str],
                                      aws_account_dict: typing.Dict, admin_session: boto3.Session,
                                      func: typing.Callable[[typing.Dict, typing.List[str], boto3.Session, argparse.Namespace], typing.NoReturn])\
        -> typing.NoReturn:
    """
    Check the regions return from collect_session_and_regions function, and process modification of members accordingly.

    Args:
        - args: An argparse.Namespace object containing parsed arguments.
        - detective_regions: A list of the region names to disable/enable Detective from, otherwise None.
        - admin_session: Detective client in the specified AWS Account and Region
        - aws_account_dict: A dictionary where the key is account ID and value is email address.
        - func: A callable function: process_accounts_disable_detective() for disable script
                                     and process_accounts_enable_detective() for enable script
    """
    if not detective_regions:
        logging.info("Execution finished without modifying any member.")
    else:
        func(aws_account_dict, detective_regions, admin_session, args)
