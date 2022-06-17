#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" python3 disableDetective.py --admin_account 555555555555 --assume_role detectiveAdmin --disabled_regions us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1 --input_file accounts.csv --skip_prompt
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

    # Setup command line arguments
    parser = argparse.ArgumentParser(description=('Unlink AWS Accounts from a central '
                                                  'Detective Account, or delete the entire Detective graph.'))
    parser.add_argument('--admin_account', type=_admin_account_type,
                        required=True,
                        help="AccountId for Central AWS Account.")
    parser.add_argument('--input_file', type=argparse.FileType('r'),
                        help=('Path to CSV file containing the list of '
                              'account IDs and Email addresses. '
                              'This does not need to be provided if you use the delete_graph flag.'))
    parser.add_argument('--assume_role', type=str, required=True,
                        help="Role Name to assume in each account.")
    parser.add_argument('--delete_graph', action='store_true',
                        help=('Delete the admin Detective graph. '
                              'If not provided, you must provide an input file.'))
    parser.add_argument('--disabled_regions', type=str,
                        help=('Regions to disable Detective. If not specified, '
                              'all available regions disabled.'))
    parser.add_argument('--skip_prompt', action='store_true',
                        help=('Skip the prompt in the script, '
                              'and answer YES to the possible prompt.'
                              'Possible prompt including:'
                              '1.Should Amazon Detective be enabled/disabled in all regions?'))
    args = parser.parse_args(args)
    if not args.delete_graph and not args.input_file:
        raise parser.error("Either an input file or the delete_graph flag should be provided.")

    return args


def delete_members(d_client: botocore.client.BaseClient, graph_arn: str,
                   account_ids: typing.List[str]) -> typing.Set[str]:
    """
    delete member accounts for all accounts in the csv that are not present in the graph member set.

    Args:
        - d_client: Detective boto3 client generated from the admin session.
        - graph_arn: Graph to add members to.
        - account_dict: Accounts read from the CSV input file.

    Returns:
        Set with the IDs of the successfully deleted accounts.
    """
    try:
        response = d_client.delete_members(GraphArn=graph_arn,
                                           AccountIds=account_ids)
        for error in response['UnprocessedAccounts']:
            logging.exception(f'Could not delete member for account {error["AccountId"]} in '
                              f'graph {graph_arn}: {error["Reason"]}')
    except Exception as e:
        logging.error(f'error when deleting member: {e}')


def process_accounts_disable_detective(aws_account_dict: typing.Dict,
                                       detective_regions: typing.List[str], admin_session: boto3.Session,
                                       args: argparse.Namespace) -> typing.NoReturn:
    """
    Process disabling in the given regions

    Args:
        - aws_account_dict: A dictionary where the key is account ID and value is email address.
        - detective_regions: A list of the region names to disable/enable Detective from, otherwise None.
        - admin_session: Detective client in the specified AWS Account and Region
        - args: An argparse.Namespace object containing parsed arguments.
    """
    # Chunk the list of accounts in the .csv into batches of 50 due to the API limitation of 50 accounts per invocation
    for chunk in helper.chunked(aws_account_dict.items(), 50):

        for region in detective_regions:
            try:
                d_client = admin_session.client('detective', region_name=region)
                graphs = helper.get_graphs(d_client)
                if not graphs:
                    logging.info(f'Amazon Detective has already been disabled in {region}')
                else:
                    logging.info(f'Disabling Amazon Detective in region {region}')

                try:
                    for graph in graphs:
                        if not args.delete_graph:
                            account_ids = [account_id for account_id, email in chunk]
                            delete_members(d_client, graph, account_ids)
                        else:
                            d_client.delete_graph(GraphArn=graph)
                except NameError as e:
                    logging.error(f'account is not defined: {e}')
                except Exception as e:
                    logging.exception(f'{e}')

            except NameError as e:
                logging.error(f'account is not defined: {e}')
            except Exception as e:
                logging.exception(f'error with region {region}: {e}')


if __name__ == '__main__':
    args = setup_command_line()
    role_session_name = "AmazonDetectiveMultiAccountScripts_DisableDetective"
    aws_account_dict = helper.read_accounts_csv(args.input_file)

    # making sure that we either have an account list to delete from graphs or the delete_graph flag is provided.
    if len(list(aws_account_dict.keys())) == 0 and not args.delete_graph:
        logging.error("The delete_graph flag was False while the provided account list is empty. "
                      "Please check your inputs and re-run the script.")
        exit(1)

    detective_regions, admin_session = helper.collect_session_and_regions(args.admin_account, args.assume_role,
                                                                          args.disabled_regions, role_session_name, args.skip_prompt)

    helper.check_region_existence_and_modify(args, detective_regions, aws_account_dict,
                                             admin_session, process_accounts_disable_detective)
