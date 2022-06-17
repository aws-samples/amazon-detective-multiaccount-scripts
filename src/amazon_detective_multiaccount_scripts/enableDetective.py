#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" python3 enableDetective.py --admin_account 555555555555 --assume_role detectiveAdmin --enabled_regions us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1 --input_file accounts.csv --skip_prompt
"""
__author__ = "Amazon Detective"
__copyright__ = "Amazon 2020"
__credits__ = "Amazon Detective"
__license__ = "Apache"
__version__ = "1.1.0"
__maintainer__ = "Amazon Detective"
__email__ = "detective-demo-requests@amazon.com"
__status__ = "Production"

import argparse
import logging
import re
import sys
import time
import typing

import boto3
import botocore.exceptions

from amazon_detective_multiaccount_scripts import amazon_detective_multiaccount_utilities as helper

FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format=FORMAT)


def setup_command_line(args=None) -> argparse.Namespace:
    """
    Configures and reads command line arguments.

    Returns:
        An argparse.Namespace object containing parsed arguments.

    Raises:
        argpare.ArgumentTypeError if an invalid value is used for
        admin_account argument.
    """
    def _admin_account_type(val: str, pattern: str = r'[0-9]{12}'):
        if not re.match(pattern, val):
            raise argparse.ArgumentTypeError
        return val

    class ParseCommaSeparatedKeyValuePairsAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, dict())
            for kv_pairs in values.split(","):
                key, _, value = kv_pairs.partition('=')
                getattr(namespace, self.dest)[key] = value

    # Setup command line arguments
    parser = argparse.ArgumentParser(description=('Link AWS Accounts to central '
                                                  'Detective Account.'))
    parser.add_argument('--admin_account', type=_admin_account_type,
                        required=True,
                        help="AccountId for Central AWS Account.")
    parser.add_argument('--input_file', type=argparse.FileType('r'),
                        required=True,
                        help=('Path to CSV file containing the list of '
                              'account IDs and Email addresses.'))
    parser.add_argument('--assume_role', type=str, required=True,
                        help="Role Name to assume in each account.")
    parser.add_argument('--enabled_regions', type=str,
                        help=('Regions to enable Detective. If not specified, '
                              'all available regions enabled.'))
    parser.add_argument('--disable_email', action='store_true',
                        help=('Don\'t send emails to the member accounts. Member '
                              'accounts must still accept the invitation before '
                              'they are added to the behavior graph.'))
    parser.add_argument('--skip_prompt', action='store_true',
                        help=('Skip all the prompts in the script, '
                              'and answer YES to all the possible prompts.'
                              'Possible prompts including:'
                              '1.Should Amazon Detective be enabled in certain region?'
                              '2.Should Amazon Detective be enabled/disabled in all regions?'))
    parser.add_argument('--tags',
                        action=ParseCommaSeparatedKeyValuePairsAction,
                        help='Comma-separated list of tag key-value pairs to be added '
                             'to any newly enabled Detective graphs. Values are optional '
                             'and are separated from keys by the equal sign (i.e. \'=\')')
    return parser.parse_args(args)


def create_members(d_client: botocore.client.BaseClient, graph_arn: str, disable_email: bool, account_ids: typing.Set[str],
                   account_csv: typing.Dict[str, str]) -> typing.Set[str]:
    """
    Creates member accounts for all accounts in the csv that are not present in the graph member set.

    Args:
        - d_client: Detective boto3 client generated from the admin session.
        - graph_arn: Graph to add members to.
        - account_ids: Already present account ids in the graph.
        - account_csv: Accounts read from the CSV input file.

    Returns:
        Set with the IDs of the successfully created accounts.
    """
    try:
        # I'm calculating set difference: the elements that are present in the CSV and that are not
        # present in the account_ids set.
        set_difference = account_csv.keys() - account_ids
        if not set_difference:
            logging.info(f'No new members to create in graph {graph_arn}.')
            return set()

        logging.info(f'Creating member accounts in graph {graph_arn} '
                     f'for accounts {", ".join(set_difference)}.')

        new_members = [{'AccountId': x, 'EmailAddress': account_csv[x]}
                       for x in set_difference]
        response = d_client.create_members(GraphArn=graph_arn,
                                           Message='Automatically generated invitation',
                                           Accounts=new_members,
                                           DisableEmailNotification=disable_email)
        for error in response['UnprocessedAccounts']:
            logging.exception(f'Could not create member for account {error["AccountId"]} in '
                              f'graph {graph_arn}: {error["Reason"]}')
    except Exception as e:
        logging.exception(f'exception when getting memebers: {e}')
    return {x['AccountId'] for x in response['Members']}


def accept_invitations(role: str, accounts: typing.Set[str], graph: str, region: str) -> typing.NoReturn:
    """
    Accept invitation for a list of accounts in a given graph.

    Args:
        - role: Role to assume when accepting the invitation.
        - accounts: Set of accounts pending to accept.
        - graph: Graph the accounts are being invited to.
        - region: Region for the client
    """
    role_session_name = "AmazonDetectiveMultiAccountScripts_AcceptInvitations"
    try:
        for account in accounts:
            logging.info(
                f'Accepting invitation for account {account} in graph {graph}.')
            session = helper.assume_role(account, role, role_session_name)
            local_client = session.client('detective', region_name=region)
            local_client.accept_invitation(GraphArn=graph)
    except Exception as e:
        logging.exception(f'error accepting invitation {e.args}')


def enable_detective(d_client: botocore.client.BaseClient, region: str, skip_prompt: bool, tags: dict = {}):
    """
    Enabling Amazon Detective in the given region

    Args:
        - d_client: Detective boto3 client generated from the admin session.
        - region: A region string that is going to be enabled
        - skip_prompt: Customer agree to skip the prompt and agree to make the change
        - tags: A list of tag key-value pairs to be added to the newly enabled Detective graphs
    """
    # Initialize the confirm variable
    confirm = 'N'
    graphs = helper.get_graphs(d_client)

    if not graphs:
        if not skip_prompt:
            confirm = input('Should Amazon Detective be enabled in {}? Enter [Y/N]: '.format(region))
        if skip_prompt or confirm == 'Y' or confirm == 'y':
            logging.info(f'Enabling Amazon Detective in {region}' + (f' with tags {tags}' if tags else ''))
            if not tags:
                graphs = [d_client.create_graph()['GraphArn']]
            else:
                graphs = [d_client.create_graph(Tags=tags)['GraphArn']]
        else:
            logging.info(f'Skipping {region}')
            return None
        logging.info(f'Amazon Detective is enabled in region {region}')
    return graphs


def process_accounts_enable_detective(aws_account_dict: typing.Dict,
                                      detective_regions: typing.List[str], admin_session: boto3.Session,
                                      args: argparse.Namespace) -> typing.NoReturn:
    """
    Process enabling in the given regions

    Args:
        - aws_account_dict: A dictionary where the key is account ID and value is email address.
        - detective_regions: A list of the region names to disable/enable Detective from, otherwise None.
        - admin_session: Detective client in the specified AWS Account and Region
        - args: An argparse.Namespace object containing parsed arguments.
    """
    # Chunk the list of accounts in the .csv into batches of 50 due to the API limitation of 50 accounts per invocation
    for chunk_tuple in helper.chunked(aws_account_dict.items(), 50):
        chunk = {x: y for x, y in chunk_tuple}

        for region in detective_regions:
            try:
                d_client = admin_session.client('detective', region_name=region)
                graphs = enable_detective(d_client, region, args.skip_prompt, args.tags)

                if graphs is None:
                    continue

                try:
                    all_members, pending, verification_fail = helper.get_members(d_client, graphs)
                    for graph, members in all_members.items():
                        new_accounts = create_members(
                            d_client, graph, args.disable_email, members, chunk)
                        logging.info("Sleeping for 10s to allow new members' invitations to propagate.")
                        time.sleep(10)

                        # get all updated pending members from get_members()
                        updated_all_members, updated_pending, updated_verification_fail = helper.get_members(d_client, [graph])
                        recheck_set, verification_pending_set = set(), set()

                        if updated_pending:
                            for account in new_accounts:
                                if account not in updated_pending[graph]:
                                    recheck_set.add(account)

                        # Checking for 6 times makes total time 3 minutes.
                        wait_loop_count = 6
                        while wait_loop_count > 0:
                            if len(recheck_set) > 0:
                                logging.info(f'Not invited accounts found: Waiting for 30 seconds for {recheck_set} accounts')
                                time.sleep(30)
                                wait_loop_count = wait_loop_count - 1
                                updated_all_members, updated_pending, updated_verification_fail = helper.get_members(d_client, [graph])

                                for account in updated_pending[graph]:
                                    recheck_set.discard(account)

                                if updated_verification_fail:
                                    if graph in updated_verification_fail.keys():
                                        for account in updated_verification_fail[graph]:
                                            verification_pending_set.add(account)
                                            recheck_set.discard(account)
                            else:
                                wait_loop_count = 0

                        # recheck_set is for the accounts which are in invited state but excluded from accept_invitation
                        # the reason behind exclusion is these accounts are in member creation stage
                        # and race condition prevented those from acceptance
                        if len(recheck_set) > 0:
                            logging.info(f'Please recheck for {recheck_set} accounts')

                        # verification_pending_Set is for the accounts which account_id and associated email does not match
                        if len(verification_pending_set) > 0:
                            logging.info(f'Please verify account information for {verification_pending_set} accounts')

                        if len(recheck_set) > 0 or len(verification_pending_set) > 0:
                            logging.info('Please verify provided information for above listed accounts '
                                         'and run the script again with all accounts for invitation acceptance')
                            sys.exit(1)
                        else:
                            accept_invitations(args.assume_role, updated_pending[graph], graph, region)

                except NameError as e:
                    logging.error(f'account is not defined: {e}')
                except Exception as e:
                    logging.exception(f'unable to accept invitiation: {e}')

            except NameError as e:
                logging.error(f'account is not defined: {e}')
            except Exception as e:
                logging.exception(f'error with region {region}: {e}')


if __name__ == '__main__':
    args = setup_command_line()
    role_session_name = "AmazonDetectiveMultiAccountScripts_EnableDetective"
    aws_account_dict = helper.read_accounts_csv(args.input_file)

    detective_regions, admin_session = helper.collect_session_and_regions(args.admin_account, args.assume_role,
                                                                          args.enabled_regions, role_session_name, args.skip_prompt)

    helper.check_region_existence_and_modify(args, detective_regions, aws_account_dict, admin_session, process_accounts_enable_detective)