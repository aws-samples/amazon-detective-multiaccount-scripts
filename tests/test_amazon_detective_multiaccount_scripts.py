__author__ = "Amazon Detective"
__copyright__ = "Amazon 2020"
__credits__ = "Amazon Detective"
__license__ = "Apache"
__version__ = "1.1.0"
__maintainer__ = "Amazon Detective"
__email__ = "detective-demo-requests@amazon.com"
__status__ = "Production"

import itertools
import logging
import sys
from unittest.mock import Mock, patch, call

import botocore.exceptions
import botocore.session
import pytest
import time

sys.path.append("..")

from amazon_detective_multiaccount_scripts import amazon_detective_multiaccount_utilities as helper
from amazon_detective_multiaccount_scripts import disableDetective
from amazon_detective_multiaccount_scripts import enableDetective

LOGGER = logging.getLogger(__name__)

"""
    This test scripts cover all the lines
    from enableDetective.py, disableDetective.py, amazon_detective_multiaccount_utilities.py
    Except:
    amazon_detective_multiaccount_utilities.py:              Assume_role function (the normal case)
    disableDetective.py:                                     __main__ function
    enableDetective.py:                                      __main__ function
"""


@pytest.mark.xfail
def test_that_you_wrote_tests():
    from textwrap import dedent

    assertion_string = dedent(
        """\
    No, you have not written tests.

    However, unless a test is run, the pytest execution will fail
    due to no tests or missing coverage. So, write a real test and
    then remove this!
    """
    )
    assert False, assertion_string


def test_amazon_detective_multiaccount_scripts_importable():
    import amazon_detective_multiaccount_scripts  # noqa: F401


###
# The purpose of this test is to make sure our internal method _admin_account_type() deals with admin accounts correctly
# and the rest of the inputs are parsed correctly as well in enableDetective.py.
###
def test_setup_command_line_enable_detective():

    args = enableDetective.setup_command_line(['--admin_account', '555555555555', '--assume_role', 'detectiveAdmin', '--enabled_regions',
                                               'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])
    assert args.admin_account == '555555555555'
    assert args.assume_role == 'detectiveAdmin'
    assert args.enabled_regions == 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1'
    assert not args.disable_email
    assert not args.skip_prompt

    args = enableDetective.setup_command_line(['--admin_account', '012345678901', '--assume_role', 'detectiveAdmin', '--input_file', 'accounts.csv'])
    assert args.admin_account == '012345678901'
    assert not args.enabled_regions

    args = enableDetective.setup_command_line(['--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--enabled_regions',
                                               'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])
    assert args.admin_account == '000000000001'
    assert not args.tags

    args = enableDetective.setup_command_line("--admin_account 123456789012 --assume_role detectiveAdmin --input_file accounts.csv "
                                              "--tags TagKey1=TagValue1,TagKey2=TagValue2,TagKey3=TagValue3,TagKey4=,TagKey5=TagValue5,TagKey6".split(" "))
    assert args.tags == {
        "TagKey1": "TagValue1",
        "TagKey2": "TagValue2",
        "TagKey3": "TagValue3",
        "TagKey4": "",
        "TagKey5": "TagValue5",
        "TagKey6": "",
    }

    args = enableDetective.setup_command_line(['--disable_email', '--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--input_file',
                                               'accounts.csv'])
    assert args.disable_email

    args = enableDetective.setup_command_line(['--disable_email', '--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--input_file',
                                               'accounts.csv', '--skip_prompt'])
    assert args.skip_prompt

    # Wrong admin account
    # The internal function _admin_account_type() should raise argparse.ArgumentTypeError,
    # however this exception gets supressed by argparse, and SystemExit is raised instead.
    with pytest.raises(SystemExit):
        enableDetective.setup_command_line(['--admin_account', '12345', '--assume_role', 'detectiveAdmin', '--enabled_regions',
                                            'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])

    # Nonexistent input file
    with pytest.raises(SystemExit):
        enableDetective.setup_command_line(['--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--enabled_regions',
                                            'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts1.csv'])

    # Nonexistent argument
    with pytest.raises(SystemExit):
        enableDetective.setup_command_line(['--guest_account', '000000000001', '--assume_role', 'detectiveAdmin', '--enabled_regions',
                                            'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])


###
# The purpose of this test is to make sure our internal method _admin_account_type() deals with admin accounts correctly
# and the rest of the inputs are parsed correctly as well in disableDetective.py.
###
def test_setup_command_line_disable_detective():

    args = disableDetective.setup_command_line(['--admin_account', '555555555555', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                                'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])
    assert args.admin_account == '555555555555'
    assert args.assume_role == 'detectiveAdmin'
    assert args.disabled_regions == 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1'
    assert not args.skip_prompt

    args = disableDetective.setup_command_line(['--admin_account', '012345678901', '--assume_role', 'detectiveAdmin', '--input_file', 'accounts.csv'])
    assert args.admin_account == '012345678901'
    assert not args.disabled_regions

    args = disableDetective.setup_command_line(['--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                                'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])
    assert args.admin_account == '000000000001'

    args = disableDetective.setup_command_line(['--admin_account', '012345678901', '--assume_role', 'detectiveAdmin',
                                                '--input_file', 'accounts.csv', '--skip_prompt'])
    assert args.skip_prompt
    assert not args.disabled_regions

    # Wrong admin account
    # The internal function _admin_account_type() should raise argparse.ArgumentTypeError,
    # however this exception gets suppressed by argparse, and SystemExit is raised instead.
    with pytest.raises(SystemExit):
        disableDetective.setup_command_line(['--admin_account', '12345', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                             'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])

    # Nonexistent input file and no delete_graph flag
    with pytest.raises(SystemExit):
        disableDetective.setup_command_line(['--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                             'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts1.csv'])

    # Nonexistent input file with delete_graph flag provided
    with pytest.raises(SystemExit):
        disableDetective.setup_command_line(['--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                             'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts1.csv', '--delete_graph'])

    # No input file provided and no delete_graph flag
    with pytest.raises(SystemExit):
        disableDetective.setup_command_line(['--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                             'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1'])

    # No input file provided but delete_graph is set
    args = disableDetective.setup_command_line(['--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                                'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--delete_graph'])
    assert not args.input_file
    assert args.delete_graph

    # Nonexistent argument get past to the function
    with pytest.raises(SystemExit):
        disableDetective.setup_command_line(['--guest_account', '555555555555', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                            'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])


###
# The purpose of this test is to make sure we read accounts and emails correctly from the input .csv file when
# using in enableDetective.py
###
def test_read_accounts_csv_enable_detective():
    args = enableDetective.setup_command_line(['--admin_account', '555555555555', '--assume_role', 'detectiveAdmin', '--enabled_regions',
                                               'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])

    accounts_dict = helper.read_accounts_csv(args.input_file)

    assert len(accounts_dict.keys()) == 6
    assert accounts_dict == {"123456789012": "random@gmail.com", "000012345678": "email@gmail.com", "555555555555": "test5@gmail.com",
                             "111111111111": "test1@gmail.com", "222222222222": "test2@gmail.com", "333333333333": "test3@gmail.com"}


###
# The purpose of this test is to make sure we read accounts and emails correctly from the input .csv file when
# using in disableDetective.py
###
def test_read_accounts_csv_disable_detective():
    # a test case where an input file is provided, although some lines are not correct
    args = disableDetective.setup_command_line(['--admin_account', '555555555555', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                                'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])

    with patch.object(logging, 'error') as mock_log_error:
        accounts_dict = helper.read_accounts_csv(args.input_file)
    assert mock_log_error.call_count == 3
    assert len(accounts_dict.keys()) == 6
    assert accounts_dict == {"123456789012": "random@gmail.com", "000012345678": "email@gmail.com", "555555555555": "test5@gmail.com",
                             "111111111111": "test1@gmail.com", "222222222222": "test2@gmail.com", "333333333333": "test3@gmail.com"}

    # a test case where no input file is provided
    args = disableDetective.setup_command_line(['--admin_account', '555555555555', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                                'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--delete_graph'])
    assert not args.input_file
    accounts_dict = helper.read_accounts_csv(args.input_file)
    assert accounts_dict == {}

    # a test case where an empty input file is provided, along with delete_graph. This is not an error, although clients should not run with this kind of input
    args = disableDetective.setup_command_line(['--admin_account', '555555555555', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                                'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts2.csv', '--delete_graph'])
    accounts_dict = helper.read_accounts_csv(args.input_file)
    assert accounts_dict == {}
    assert args.delete_graph


###
# The purpose of this test is to make sure we extract regions correctly in amazon_detective_multiaccount_utilities.py
###
def test_get_regions_amazon_detective_multiaccount_utilities():
    args = enableDetective.setup_command_line(['--disable_email', '--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--input_file',
                                               'accounts.csv'])
    # If user_regions is provided by user
    session_test = Mock()
    regions = helper.get_regions(session_test, args.skip_prompt, 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1')
    assert regions == ['us-east-1', 'us-east-2', 'us-west-2', 'ap-northeast-1', 'eu-west-1']

    # If user_regions is an empty string, and answer yes
    boto_session = Mock()
    boto_session.get_available_regions.return_value = ['us-east-1', 'us-east-2']
    with patch('builtins.input', return_value='Y'):
        regions = helper.get_regions(boto_session, args.skip_prompt, '')
    assert regions == ['us-east-1', 'us-east-2']

    # If Regions is not passed, and answered yes
    with patch('builtins.input', return_value='Y'):
        regions = helper.get_regions(boto_session, args.skip_prompt)
    assert regions == ['us-east-1', 'us-east-2']

    # If Regions is not passed, and answered no
    with patch('builtins.input', return_value='N'):
        regions = helper.get_regions(boto_session, args.skip_prompt)
    assert not regions

    # If Regions is not passed, and answered random word
    with patch('builtins.input', return_value='///detective'):
        regions = helper.get_regions(boto_session, args.skip_prompt)
    assert not regions

    # If customer pass in skip_prompt option
    args = enableDetective.setup_command_line(['--disable_email', '--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--input_file',
                                               'accounts.csv', '--skip_prompt'])
    regions = helper.get_regions(boto_session, args.skip_prompt, '')
    assert regions == ['us-east-1', 'us-east-2']


###
# The purpose of this test is to make sure the exception case of assume_role()
# runs correctly in amazon_detective_multiaccount_utilities.py
###
def test_assume_role_exception_detective_multiaccount_utilities():
    # Exception case test: invalid input
    with pytest.raises(Exception):
        helper.assume_role("123456789012", "DetectiveAdmin")


###
# The purpose of this test is to make sure we could throw exception in get_graphs() function
# in amazon_detective_multiaccount_utilities.py
###
def test_get_graphs_exception_detective_multiaccount_utilities():
    d_client = Mock()
    d_client.list_graphs.side_effect = botocore.exceptions.EndpointConnectionError(endpoint_url='https://ec2.us-weast-1.amazonaws.com/')
    assert helper.get_graphs(d_client) == []


###
# The purpose of this test is to make sure get_members() runs correctly in amazon_detective_multiaccount_utilities.py
###
def test_get_members_detective_multiaccount_utilities():
    d_client = Mock()
    d_client1 = Mock()
    d_client2 = Mock()

    # Test case where we have both active and pending accounts
    d_client.list_members.return_value = {"MemberDetails": [{"AccountId": "123456789012", "Status": "ENABLED"},
                                                            {"AccountId": "111111111111", "Status": "ENABLED"},
                                                            {"AccountId": "222222222222", "Status": "INVITED"},
                                                            {"AccountId": "333333333333", "Status": "VERIFICATION_FAILED"}]}

    # Check correctness (with 2 specified graphs)
    all_ac, pending, verification_fail = helper.get_members(d_client, ["graph1", "graph2"])

    assert all_ac == {"graph1": {"123456789012", "111111111111", "222222222222", "333333333333"},
                      "graph2": {"123456789012", "111111111111", "222222222222", "333333333333"}}
    assert pending == {"graph1": {"222222222222"}, "graph2": {"222222222222"}}
    assert verification_fail == {'graph1': {"333333333333"}, 'graph2': {"333333333333"}}

    # If return value from list_members contains NextToken
    d_client1.list_members.side_effect = [{"MemberDetails": [{"AccountId": "111111111111", "Status": "ENABLED"}], "NextToken": None}, KeyError()]
    with pytest.raises(KeyError):
        helper.get_members(d_client1, ["graph1"])

    # Test case with no pending accounts
    d_client.list_members.return_value = {"MemberDetails": [{"AccountId": "111111111111", "Status": "ENABLED"}]}

    # Check correctness (with 1 specified graph)
    all_ac, pending, verification_fail = helper.get_members(d_client, ["graph1"])

    assert all_ac == {"graph1": {"111111111111"}}
    assert pending == {"graph1": set()}
    assert verification_fail == {"graph1": set()}

    # Test on Get Members' Exception by passing invalid argument:
    with pytest.raises(Exception):
        helper.get_members(d_client1, d_client2)


###
# The purpose of this test is to make sure chunked() runs correctly in amazon_detective_multiaccount_utilities.py
###
def test_chunked():
    # Test on valid input
    dict_obj = {"123456789012": "random@gmail.com", "000012345678": "email@gmail.com", "555555555555": "test5@gmail.com", "111111111111": "test1@gmail.com",
                "222222222222": "test2@gmail.com", "333333333333": "test3@gmail.com"}
    assert tuple(helper.chunked(dict_obj.items(), 4)) == ((('123456789012', 'random@gmail.com'), ('000012345678', 'email@gmail.com'),
                                                           ('555555555555', 'test5@gmail.com'), ('111111111111', 'test1@gmail.com')),
                                                          (('222222222222', 'test2@gmail.com'), ('333333333333', 'test3@gmail.com')))

    # Test on the exception case when input is invalid
    with patch.object(itertools, "islice", iter(())):
        helper.chunked(dict_obj.items(), 100)


###
# The purpose of this test is to make sure create_members() runs correctly in enableDetective.py
###
def test_create_members_enable_detective():
    d_client = Mock()

    # The existing members and new required members don't overlap. Creation causes no errors.
    d_client.create_members.return_value = {'UnprocessedAccounts': {}, 'Members': [{"AccountId": "111111111111"}, {"AccountId": "222222222222"}]}

    created_members = enableDetective.create_members(d_client, "graph1", False, {"333333333333"},
                                                     {"111111111111": "1@gmail.com", "222222222222": "2@gmail.com"})
    assert created_members == {"111111111111", "222222222222"}

    # The existing members and new required members overlap by one account. Creation causes no errors.
    d_client.create_members.return_value = {'UnprocessedAccounts': {}, 'Members': [{"AccountId": "111111111111"}]}

    created_members = enableDetective.create_members(d_client, "graph1", False, {"222222222222"},
                                                     {"111111111111": "1@gmail.com", "222222222222": "2@gmail.com"})
    assert created_members == {"111111111111"}

    # All required members already exist. Creation causes no errors.
    d_client.create_members.return_value = {'UnprocessedAccounts': {}, 'Members': []}

    created_members = enableDetective.create_members(d_client, "graph1", False, {"111111111111", "222222222222", "333333333333"},
                                                     {"111111111111": "1@gmail.com", "222222222222": "2@gmail.com"})
    assert created_members == set()

    # The existing members and new required members don't overlap. Creation causes 1 error.
    d_client.create_members.return_value = {'UnprocessedAccounts': {"AccountId": "111111111111", "Reason": "some_reason"},
                                            'Members': [{"AccountId": "222222222222"}]}

    created_members = enableDetective.create_members(d_client, "graph1", False, {"333333333333"}, {"111111111111": "1@gmail.com",
                                                                                                   "222222222222": "2@gmail.com"})
    assert created_members == {"222222222222"}

    # Test the disabled email flag is properly passed through
    enableDetective.create_members(d_client, "with_email", False, {"333333333333"}, {"111111111111": "1@gmail.com"})
    d_client.create_members.assert_called_with(GraphArn="with_email",
                                               Message='Automatically generated invitation',
                                               Accounts=[{'AccountId': '111111111111', 'EmailAddress': '1@gmail.com'}],
                                               DisableEmailNotification=False)

    enableDetective.create_members(d_client, "without_email", False, {"333333333333"}, {"111111111111": "1@gmail.com"})
    d_client.create_members.assert_called_with(GraphArn="without_email",
                                               Message='Automatically generated invitation',
                                               Accounts=[{'AccountId': '111111111111', 'EmailAddress': '1@gmail.com'}],
                                               DisableEmailNotification=False)


###
# The purpose of this test is to make sure the exception case in accept_invitations() runs correctly in enableDetective.py
###
def test_accept_invitations_exception_enable_detective():
    # Check exception case by passing incorrect argument
    with patch.object(logging, 'exception') as mock_log_exception:
        enableDetective.accept_invitations("admin", '111111111111', "graph1", "us-east-2")
        mock_log_exception.assert_called()


###
# The purpose of this test is to make sure accept_invitations() runs correctly in enableDetective.py
###
def test_accept_invitations_enable_detective():
    # In normal calling case, logging.info() should be called twice: 1. in accept_invitations, 2. in assume_role
    with patch.object(logging, 'info') as mock_log_info:
        enableDetective.accept_invitations("admin", {"111111111111"}, "graph1", "us-east-2")
        assert mock_log_info.call_count == 2

    # In normal calling case, helper.assume_role() should be called
    with patch.object(helper, 'assume_role') as helper_assume_role_mock:
        enableDetective.accept_invitations("admin", {"111111111111"}, "graph1", "us-east-2")
        helper_assume_role_mock.assert_called_once()


###
# The purpose of this test is to make sure enable_detective() runs correctly in enableDetective.py
###
def test_enable_detective():
    d_client = Mock()
    # args without tags
    args = enableDetective.setup_command_line(['--disable_email', '--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--input_file',
                                               'accounts.csv'])
    # args with tags
    args1 = enableDetective.setup_command_line("--admin_account 123456789012 --assume_role detectiveAdmin --input_file accounts.csv "
                                               "--tags TagKey1=TagValue1,TagKey2=TagValue2,TagKey3=TagValue3,TagKey4=,TagKey5=TagValue5,TagKey6".split(" "))
    # If all three inputs are passed, and d_client has graphs without tags
    with patch.object(helper, "get_graphs", return_value=["graph1"]):
        graph = enableDetective.enable_detective(d_client, "us-east-2", args.skip_prompt, {})
        assert graph == ["graph1"]

    d_client.list_graphs.return_value = {'GraphList': []}
    d_client.create_graph.return_value = {'GraphArn': 'fooGraph123'}

    # If d_client has no graph, and the input is 'Y', test for normal "yes" case
    with patch('builtins.input', return_value='Y'):
        assert enableDetective.enable_detective(d_client, "us-east-2", args.skip_prompt) == ['fooGraph123']
        with patch.object(logging, 'info') as mock_log_info:
            enableDetective.enable_detective(d_client, "us-east-2", args.skip_prompt)
            assert mock_log_info.call_count == 2

    # If d_client has no graph and customer indicated tags, and the input is 'Y', test for normal "yes" case
    with patch('builtins.input', return_value='Y'):
        enableDetective.enable_detective(d_client, "us-east-2", args1.skip_prompt, args1.tags)
        d_client.create_graph.assert_called_with(Tags={'TagKey1': 'TagValue1', 'TagKey2': 'TagValue2',
                                                       'TagKey3': 'TagValue3', 'TagKey4': '', 'TagKey5': 'TagValue5', 'TagKey6': ''})

    # If d_client has no graph, and the input is 'N', test for normal "no" case
    with patch('builtins.input', return_value='N'):
        assert not enableDetective.enable_detective(d_client, "us-east-2", args.skip_prompt)
        with patch.object(logging, 'info') as mock_log_info:
            enableDetective.enable_detective(d_client, "us-east-2", args.skip_prompt)
            assert mock_log_info.call_count == 1

    # If d_client has no graph, and if customer pass in skip_prompt option
    args1 = enableDetective.setup_command_line(['--disable_email', '--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--input_file',
                                               'accounts.csv', '--skip_prompt'])
    assert enableDetective.enable_detective(d_client, "us-east-2", args1.skip_prompt) == ['fooGraph123']
    with patch.object(logging, 'info') as mock_log_info_again:
        enableDetective.enable_detective(d_client, "us-east-2", args1.skip_prompt)
    assert mock_log_info_again.call_count == 2


###
# The purpose of this test is to make sure Exception case in delete_members() runs correctly in disableDetective.py
###
def test_exception_delete_members_disable_detective():
    d_client = Mock()

    # Exception case test by passing invalid argument
    with patch.object(logging, 'error') as mock_log_error:
        disableDetective.delete_members(d_client, "graph1", "222222222222")
    assert mock_log_error.call_count == 1


###
# The purpose of this test is to make sure delete_members() runs correctly in disableDetective.py
###
def test_delete_members_disable_detective():
    d_client = Mock()
    # Test the flag is properly passed through
    list_obj = ['111111111111', '222222222222']
    disableDetective.delete_members(d_client, "with_email", list_obj)
    d_client.delete_members.assert_called_with(GraphArn="with_email", AccountIds=['111111111111', '222222222222'])

    # Test normal case
    d_client.delete_members.return_value = {"AccountId": ['111111111111', '222222222222']}
    disableDetective.delete_members(d_client, "graph1", list_obj)

    # Has "unprocessedAccount" case
    d_client.delete_members.return_value = {'UnprocessedAccounts': [{"AccountId": "111111111111", "Reason": "some_reason"}]}
    with patch.object(logging, 'exception') as mock_log_exception:
        disableDetective.delete_members(d_client, "graph1", list_obj)
        mock_log_exception.assert_called_once()


###
# The purpose of this test is to make sure exception brunch in collect_session_and_regions()
# runs correctly in amazon_detective_multiaccount_utilities.py
###
def test_exception_collect_session_and_regions():
    admin_account = '555555555555'
    assume_role = 'detectiveAdmin'
    role_session_name = "AmazonDetectiveMultiAccountScripts"
    regions = 'us-east-1, us-east-2'
    args = enableDetective.setup_command_line(['--disable_email', '--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--input_file',
                                               'accounts.csv', '--skip_prompt'])
    # Since the code should never arrive to the exception clause,
    # We purposely raise the exception to check this branch could work
    helper.assume_role = Mock(side_effect=Exception)
    # Exception error
    with patch.object(logging, 'exception') as mock_log_exception:
        helper.collect_session_and_regions(admin_account, assume_role, regions, role_session_name, args.skip_prompt)
        assert mock_log_exception.call_count == 1


###
# The purpose of this test is to make sure NameError brunch in collect_session_and_regions()
# runs correctly in amazon_detective_multiaccount_utilities.py
###
def test_name_error_collect_session_and_regions():
    admin_account = '555555555555'
    assume_role = 'detectiveAdmin'
    role_session_name = Mock()
    regions = 'us-east-1, us-east-2'
    args = enableDetective.setup_command_line(['--disable_email', '--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--input_file',
                                               'accounts.csv', '--skip_prompt'])

    # Test NameError exception by raising NameError purposely
    # since other than using undefined variable in the script, there are
    # no other way to trigger the NameError.
    helper.assume_role = Mock(side_effect=NameError)
    with patch.object(logging, 'error') as mock_log_error:
        helper.collect_session_and_regions(admin_account, assume_role, regions, role_session_name, args.skip_prompt)
        assert mock_log_error.call_count == 1


###
# The purpose of this test is to make sure normal case in collect_session_and_regions()
# runs correctly in amazon_detective_multiaccount_utilities.py
###
def test_collect_session_and_regions():
    role_session_name = "AmazonDetectiveMultiAccountScripts"
    # Using enableDetective args to test on normal behavior
    args = enableDetective.setup_command_line(['--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--enabled_regions',
                                               'us-east-1,us-east-2,us-west-2', '--input_file', 'accounts.csv'])
    with patch.object(helper, 'assume_role', return_value=["session1", "session2"]):
        detective_regions, admin_session = helper.collect_session_and_regions(args.admin_account, args.assume_role, args.enabled_regions,
                                                                              role_session_name, args.skip_prompt)
        assert detective_regions == ['us-east-1', 'us-east-2', 'us-west-2']
        assert admin_session == ["session1", "session2"]

    # Using disableDetective args to test on normal behavior
    args = disableDetective.setup_command_line(['--admin_account', '555555555555', '--assume_role', 'detectiveAdmin', '--disabled_regions',
                                                'us-east-1,us-east-2,us-west-2,ap-northeast-1', '--input_file', 'accounts.csv'])
    with patch.object(helper, 'assume_role', return_value=["session1"]):
        detective_regions, admin_session = helper.collect_session_and_regions(args.admin_account, args.assume_role, args.disabled_regions,
                                                                              role_session_name, args.skip_prompt)
        assert detective_regions == ['us-east-1', 'us-east-2', 'us-west-2', 'ap-northeast-1']
        assert admin_session == ["session1"]

    # If regions does not exist and user answer yes to input request question,
    # detective_regions prints out all 20 regions
    args = enableDetective.setup_command_line(['--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--input_file', 'accounts.csv'])
    assert not args.enabled_regions
    with patch.object(helper, 'assume_role', return_value=["session1", "session2"]):
        with patch('builtins.input', return_value='Y'):
            detective_regions, admin_session = helper.collect_session_and_regions(args.admin_account, args.assume_role, args.enabled_regions,
                                                                                  role_session_name, args.skip_prompt)
            assert len(detective_regions) == 20
            assert admin_session == ["session1", "session2"]

    # mocking function returns to test on normal behavior
    args = Mock()
    regions = 'us-east-1, us-east-2'
    args.admin_account = "123456789101"
    args.assume_role = "admin"

    with patch.object(helper, 'get_regions', return_value=['us-east-1', 'us-east-2']):
        with patch.object(helper, 'assume_role', return_value=["session1", "session2"]):
            detective_regions, admin_session = helper.collect_session_and_regions(args.admin_account, args.assume_role, regions,
                                                                                  role_session_name, args.skip_prompt)
            assert detective_regions == ['us-east-1', 'us-east-2']
            assert admin_session == ["session1", "session2"]

    # If customer pass in skip_prompt option
    args1 = enableDetective.setup_command_line(['--disable_email', '--admin_account', '000000000001', '--assume_role', 'detectiveAdmin', '--input_file',
                                               'accounts.csv', '--skip_prompt'])
    with patch.object(helper, 'get_regions', return_value=['us-east-1', 'us-east-2']):
        with patch.object(helper, 'assume_role', return_value=["session1", "session2"]):
            detective_regions, admin_session = helper.collect_session_and_regions(args.admin_account, args.assume_role, regions,
                                                                                  role_session_name, args1.skip_prompt)
            assert detective_regions == ['us-east-1', 'us-east-2']
            assert admin_session == ["session1", "session2"]


###
# The purpose of this test is to make sure when gathering d_client and graphs
# in process_accounts_enable_detective(), the error and exception brunch
# run correctly in enableDetective.py
###
def test_first_layer_process_accounts_enable_detective():
    args = Mock()
    admin_session = Mock()
    aws_account_dict = {"123456789012": "random@gmail.com", "000012345678": "email@gmail.com", "555555555555": "test5@gmail.com",
                        "111111111111": "test1@gmail.com", "222222222222": "test2@gmail.com", "333333333333": "test3@gmail.com"}
    detective_regions = ['us-east-1', 'us-east-2', 'us-west-2']
    detective_regions2 = ['us-east-1']
    regions_error = 'abcdefg'

    # Exception case when enabling detective by passing invalid regions
    # logging.exception will be called 7 times because len(regions_error) == 7
    with patch.object(logging, 'exception') as mock_log_exception:
        enableDetective.process_accounts_enable_detective(aws_account_dict, regions_error, admin_session, args)
        # Has 7 characters in the invalid regions, so the for loop runs 7 times
        assert mock_log_exception.call_count == 7

    # test NameError case when enabling detective by purposely raising the error
    # since other than using undefined variable in the script, there are
    # no other way to trigger the NameError.
    admin_session.client = Mock(side_effect=NameError)
    with patch.object(logging, 'error') as mock_log_error:
        enableDetective.process_accounts_enable_detective(aws_account_dict, detective_regions, admin_session, args)
        # Has 3 regions, so the for loop runs three times
        assert mock_log_error.call_count == 3

    # If graphs is none
    enableDetective.enable_detective = Mock(return_value=None)
    # Assert that no additional methods were called
    with patch.object(helper, 'get_members') as check_helper_get_members:
        enableDetective.process_accounts_enable_detective(aws_account_dict, detective_regions2, admin_session, args)
        assert check_helper_get_members.call_count == 0


###
# The purpose of this test is to make sure when process the enable functions
# in process_accounts_enable_detective(), the error and exception brunch
# run correctly in enableDetective.py
###
def test_second_layer_process_accounts_enable_detective():
    args = Mock()
    admin_session = Mock()
    aws_account_dict = {"123456789012": "random@gmail.com", "000012345678": "email@gmail.com", "555555555555": "test5@gmail.com",
                        "111111111111": "test1@gmail.com", "222222222222": "test2@gmail.com", "333333333333": "test3@gmail.com"}
    #
    detective_regions1 = ['us-east-2']
    detective_regions2 = ['us-east-1', 'us-east-2', 'us-west-2']
    # Exception case after getting d_client and graphs
    enableDetective.enable_detective = Mock(return_value=["graph1"])
    admin_session.client = Mock(return_value=Mock())
    helper.get_members = Mock(side_effect=[{"graph1": {"111111111111"}}, {"graph1": set()}, {"graph1": set()}])
    enableDetective.create_members = Mock(return_value={"111111111111"})
    args.assume_role = None

    # Trigger exception by failing the accept_invitations function.
    with patch.object(logging, 'exception') as mock_log_exception:
        enableDetective.process_accounts_enable_detective(aws_account_dict, detective_regions1, admin_session, args)
        # Has 1 regions, so the for loop runs once
        assert mock_log_exception.call_count == 1

    # test NameError case when enabling detective by purposely raising the error
    # since other than using undefined variable in the script, there are
    # no other way to trigger the NameError.
    helper.get_members = Mock(side_effect=NameError)
    with patch.object(logging, 'error') as mock_log_error:
        enableDetective.process_accounts_enable_detective(aws_account_dict, detective_regions2, admin_session, args)
        # Has 3 regions, so the for loop runs three times
        assert mock_log_error.call_count == 3


###
# The purpose of this test is to make sure process_accounts_enable_detective()
# run correctly in enableDetective.py
###
def test_additionally_process_accounts_enable_detective():

    args = Mock()
    args.assume_role = None
    detective_regions1 = ['us-east-2']
    aws_account_dict = {"123456789012": "random@gmail.com", "111111111111": "test1@gmail.com",
                        "222222222222": "test2@gmail.com", "333333333333": "test3@gmail.com"}
    admin_session = Mock()
    admin_session.client = Mock(return_value=Mock())

    enableDetective.enable_detective = Mock(return_value=None)

    # If graph return is None from enable_detective()
    with patch.object(helper, 'get_members') as get_member_mock:
        enableDetective.process_accounts_enable_detective(aws_account_dict, detective_regions1, admin_session, args)
        assert get_member_mock.call_count == 0

    # If the new account was first not in the pending list nor the verification failure list,
    # and then get added to the pending list in the second run
    enableDetective.enable_detective = Mock(return_value=["graph1"])
    helper.get_members = Mock(side_effect=[[{"graph1": {"123456789012", "111111111111", "222222222222", "333333333333"}},
                                            {"graph1": set()},
                                            {"graph1": set()}],
                                           [{"graph1": {"123456789012", "111111111111", "222222222222", "333333333333"}},
                                            {"graph1": set()},
                                            {"graph1": set()}],
                                           [{"graph1": {"123456789012", "111111111111", "222222222222", "333333333333"}},
                                            {"graph1": {"222222222222"}},
                                            {"graph1": set()}]])
    enableDetective.create_members = Mock(return_value={"222222222222"})

    with patch.object(enableDetective, "accept_invitations") as accept_inv:
        with patch.object(time, 'sleep') as time_sleep:
            with patch.object(logging, 'info') as logging_info_mock:
                enableDetective.process_accounts_enable_detective(aws_account_dict, detective_regions1, admin_session, args)
                # Sleep twice since the account is in the pending list in the second run
                assert time_sleep.call_count == 2
                assert logging_info_mock.call_count == 2
                assert logging_info_mock.call_args_list == [call("Sleeping for 10s to allow new members' invitations to propagate."),
                                                            call("Not invited accounts found: Waiting for 30 seconds for {'222222222222'} accounts"),
                                                            ]
                accept_inv.assert_called_once()

    # If a graph has a new account that is not in the pending list or verification failure list
    enableDetective.enable_detective = Mock(return_value=["graph1"])
    helper.get_members = Mock(return_value=[{"graph1": {"123456789012", "111111111111", "222222222222", "333333333333"}},
                                            {"graph1": {"222222222222"}},
                                            {"graph1": {"333333333333"}}])
    enableDetective.create_members = Mock(return_value={"111111111111"})

    with pytest.raises(SystemExit) as e:
        with patch.object(time, 'sleep') as time_sleep:
            with patch.object(logging, 'info') as logging_info_mock:
                enableDetective.process_accounts_enable_detective(aws_account_dict, detective_regions1, admin_session, args)
                # one graph could be called 7 times time.sleep because recheck_set will not get empty
                assert time_sleep.call_count == 7
                assert logging_info_mock.call_count == 10
                assert logging_info_mock.call_args_list == [call("Sleeping for 10s to allow new members' invitations to propagate."),
                                                            call("Not invited accounts found: Waiting for 30 seconds for {'111111111111'} accounts"),
                                                            call("Not invited accounts found: Waiting for 30 seconds for {'111111111111'} accounts"),
                                                            call("Not invited accounts found: Waiting for 30 seconds for {'111111111111'} accounts"),
                                                            call("Not invited accounts found: Waiting for 30 seconds for {'111111111111'} accounts"),
                                                            call("Not invited accounts found: Waiting for 30 seconds for {'111111111111'} accounts"),
                                                            call("Not invited accounts found: Waiting for 30 seconds for {'111111111111'} accounts"),
                                                            call("Please recheck for {'111111111111'} accounts"),
                                                            call("Please verify account information for {'333333333333'} accounts"),
                                                            call("Please verify provided information for above listed accounts and "
                                                                 "run the script again with all accounts for invitation acceptance")
                                                            ]
                assert e.type == SystemExit

    # If two graphs have a new account that is not in the pending list or verification failure list
    enableDetective.enable_detective = Mock(return_value=["graph1"])
    helper.get_members = Mock(return_value=[{"graph1": {"123456789012", "111111111111", "222222222222", "333333333333"},
                                             "graph2": {"123456789012", "111111111111", "222222222222", "333333333333"}},
                                            {"graph1": {"222222222222"}, "graph2": {"222222222222"}},
                                            {"graph1": {"333333333333"}, "graph2": {"333333333333"}}])
    enableDetective.create_members = Mock(return_value={"111111111111"})

    with pytest.raises(SystemExit) as e:
        with patch.object(time, 'sleep') as time_sleep:
            with patch.object(logging, 'info') as logging_info_mock:
                enableDetective.process_accounts_enable_detective(aws_account_dict, detective_regions1, admin_session, args)
                # one graph could be called 7 times time.sleep because recheck_set will not get empty
                assert time_sleep.call_count == 14
                assert logging_info_mock.call_count == 20
                assert e.type == SystemExit

    # If graph has new account that is in the pending list or verification failure list
    enableDetective.enable_detective = Mock(return_value=["graph1"])
    helper.get_members = Mock(return_value=[{"graph1": {"123456789012", "111111111111", "222222222222", "333333333333"}},
                                            {"graph1": {"222222222222"}},
                                            {"graph1": {"333333333333"}}])
    enableDetective.create_members = Mock(return_value={"222222222222"})

    with patch.object(enableDetective, "accept_invitations") as accept_inv:
        with patch.object(time, 'sleep') as time_sleep:
            with patch.object(logging, 'info') as logging_info_mock:
                enableDetective.process_accounts_enable_detective(aws_account_dict, detective_regions1, admin_session, args)
                # Account 222222222222 will be sent to accept_invitations() since this account is in the pending list
                assert time_sleep.call_count == 1
                assert logging_info_mock.call_count == 1
                accept_inv.assert_called_once()


###
# The purpose of this test is to make sure when gathering d_client and graphs
# in process_accounts_disable_detective(), the error and exception brunch
# run correctly in disableDetective.py
###
def test_first_layer_process_accounts_disable_detective():
    args = Mock()
    admin_session = Mock()
    aws_account_dict = {"123456789012": "random@gmail.com", "000012345678": "email@gmail.com", "555555555555": "test5@gmail.com",
                        "111111111111": "test1@gmail.com", "222222222222": "test2@gmail.com", "333333333333": "test3@gmail.com"}

    detective_regions = ['us-east-1', 'us-east-2', 'us-west-2']
    detective_regions2 = ['us-east-1']
    regions_error = 'abcdef'

    # Has 6 characters in the invalid regions, so the for loop runs 6 times
    with patch.object(logging, 'exception') as mock_log_exception:
        disableDetective.process_accounts_disable_detective(aws_account_dict, regions_error, admin_session, args)
        # Has 6 ele
        assert mock_log_exception.call_count == 6

    # test NameError case when disabling detective by purposely raising the error
    # since other than using undefined variable in the script, there are
    # no other way to trigger the NameError.
    admin_session.client = Mock(side_effect=NameError)
    with patch.object(logging, 'error') as mock_log_error:
        disableDetective.process_accounts_disable_detective(aws_account_dict, detective_regions, admin_session, args)
        # Has 3 regions, so the for loop runs three times
        assert mock_log_error.call_count == 3

    admin_session.client = Mock(side_effect=Mock())

    # If graph is None
    helper.get_graphs = Mock(return_value=None)
    with patch.object(logging, 'info') as mock_log_info:
        disableDetective.process_accounts_disable_detective(aws_account_dict, detective_regions2, admin_session, args)
        # Has 1 regions, so the for loop runs once
        assert mock_log_info.call_count == 1
        mock_log_info.assert_called_with('Amazon Detective has already been disabled in us-east-1')

    # If graphs is not None
    helper.get_graphs = Mock(return_value=["graph1"])
    with patch.object(logging, 'info') as mock_log_info:
        disableDetective.process_accounts_disable_detective(aws_account_dict, detective_regions2, admin_session, args)
        # Has 1 regions, so the for loop runs once
        assert mock_log_info.call_count == 1
        mock_log_info.assert_called_with('Disabling Amazon Detective in region us-east-1')


###
# The purpose of this test is to make sure when process the disable functions
# in process_accounts_disable_detective(), the error and exception brunch
# run correctly in disableDetective.py
###
def test_second_layer_process_accounts_disable_detective():
    admin_session = Mock()
    args = None
    args1 = disableDetective.setup_command_line(['--admin_account', '012345678901', '--assume_role', 'detectiveAdmin', '--input_file', 'accounts.csv'])

    aws_account_dict = {"123456789012": "random@gmail.com", "000012345678": "email@gmail.com", "555555555555": "test5@gmail.com",
                        "111111111111": "test1@gmail.com", "222222222222": "test2@gmail.com", "333333333333": "test3@gmail.com"}

    detective_regions = ['us-east-1', 'us-east-2', 'us-west-2']

    admin_session.client = Mock(side_effect=Mock())
    helper.get_graphs = Mock(return_value=["graph1"])

    # Exception case after getting graphs by passing an invalid args.delete_graph
    with patch.object(logging, 'exception') as mock_log_exception:
        disableDetective.process_accounts_disable_detective(aws_account_dict, detective_regions, admin_session, args)
        # Has 3 regions, so the for loop runs three times
        assert mock_log_exception.call_count == 3

    # Normal case when args.delete_graph is None
    with patch.object(disableDetective, 'delete_members') as count_delete_members:
        disableDetective.process_accounts_disable_detective(aws_account_dict, detective_regions, admin_session, args1)
        assert count_delete_members.call_count == 3


###
# The purpose of this test is to make sure when process process_accounts_disable_detective(),
# account dict which contains accounts more than 50 could run correctly
###
def test_chunk50_accounts_disable_detective_disable_detective():
    admin_session = Mock()
    aws_account_dict = {}
    args = None

    for i in range(60):
        aws_account_dict[str(i)] = "random" + str(i) + "@gmail.com"

    detective_regions = ['us-east-1', 'us-east-2']

    disableDetective.process_accounts_disable_detective(aws_account_dict, detective_regions, admin_session, args)
    # Has 2 regions and 2 chunk due to the accounts accessed 50,so the admin_session.client ran four times
    assert admin_session.client.call_count == 4


###
# The purpose of this test is to make sure when process process_accounts_enable_detective(),
# account dict which contains accounts more than 50 could run correctly
###
def test_chunk50_accounts_disable_detective_enable_detective():
    admin_session = Mock()
    aws_account_dict = {}
    args = None

    for i in range(60):
        aws_account_dict[str(i)] = "random" + str(i) + "@gmail.com"

    detective_regions = ['us-east-1', 'us-east-2']

    enableDetective.process_accounts_enable_detective(aws_account_dict, detective_regions, admin_session, args)
    # Has 2 regions and 2 chunk due to the accounts accessed 50,so the admin_session.client ran four times
    assert admin_session.client.call_count == 4


def test_check_region_existence_and_modify():
    args = Mock()
    aws_account_dict = {}
    admin_session = Mock()
    detective_regions_none = None
    detective_regions = ['us-east-1', 'us-east-2', 'us-west-2']

    # If detective_regions is None, modification is not execute
    with patch.object(logging, "info") as mock_logging_info:
        helper.check_region_existence_and_modify(args, detective_regions_none,
                                                 aws_account_dict, admin_session, enableDetective.process_accounts_enable_detective)
    assert mock_logging_info.call_count == 1

    # If detective_regions is not None, and pass in process_accounts_enable_detective function
    with patch.object(enableDetective, "process_accounts_enable_detective") as mock_enable_process:
        helper.check_region_existence_and_modify(args, detective_regions,
                                                 aws_account_dict, admin_session, enableDetective.process_accounts_enable_detective)
    assert mock_enable_process.call_count == 1

    # If detective_regions is not None, and pass in process_accounts_disable_detective function
    with patch.object(disableDetective, "process_accounts_disable_detective") as mock_disable_process:
        helper.check_region_existence_and_modify(args, detective_regions,
                                                 aws_account_dict, admin_session, disableDetective.process_accounts_disable_detective)
    assert mock_disable_process.call_count == 1

    # If detective_regions is not None, raise exception if passing in random function
    with pytest.raises(Exception):
        helper.check_region_existence_and_modify(args, detective_regions,
                                                 aws_account_dict, admin_session, print())
