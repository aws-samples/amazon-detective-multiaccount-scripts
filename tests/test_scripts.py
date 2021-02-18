#!/usr/bin/env python3
import sys
sys.path.append("..")

import enableDetective
import disableDetective
import pytest
import argparse
from unittest.mock import Mock

###
# The purpose of this test is to make sure our internal method _master_account_type() deals with master accounts correctly and the rest of the inputs are parsed correctly as well in enableDetective.py.
###
def test_setup_command_line_enableDetective():
    
    args = enableDetective.setup_command_line(['--master_account', '555555555555', '--assume_role', 'detectiveAdmin', '--enabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])
    assert args.master_account == '555555555555'
    assert args.assume_role == 'detectiveAdmin'
    assert args.enabled_regions == 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1'

    args = enableDetective.setup_command_line(['--master_account', '012345678901', '--assume_role', 'detectiveAdmin', '--input_file', 'accounts.csv'])
    assert args.master_account == '012345678901'
    assert args.enabled_regions == None

    args = enableDetective.setup_command_line(['--master_account', '000000000001', '--assume_role', 'detectiveAdmin', '--enabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])
    assert args.master_account == '000000000001'
    assert args.tags == None

    args = enableDetective.setup_command_line("--master_account 123456789012 --assume_role detectiveAdmin --input_file accounts.csv --tags TagKey1=TagValue1,TagKey2=TagValue2,TagKey3=TagValue3".split(" "))
    assert args.tags == {
        "TagKey1": "TagValue1",
        "TagKey2": "TagValue2",
        "TagKey3": "TagValue3",
    }

    # Wrong master account
    # The internal function _master_account_type() should raise argparse.ArgumentTypeError, however this exception gets supressed by argparse, and SystemExit is raised instead.
    with pytest.raises(SystemExit):
    	enableDetective.setup_command_line(['--master_account', '12345', '--assume_role', 'detectiveAdmin', '--enabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])
    
    # Non existent input file
    with pytest.raises(SystemExit):
    	enableDetective.setup_command_line(['--master_account', '000000000001', '--assume_role', 'detectiveAdmin', '--enabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts1.csv'])
    

###
# The purpose of this test is to make sure our internal method _master_account_type() deals with master accounts correctly and the rest of the inputs are parsed correctly as well in disableDetective.py.
###
def test_setup_command_line_disableDetective():
    
    args = disableDetective.setup_command_line(['--master_account', '555555555555', '--assume_role', 'detectiveAdmin', '--disabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])
    assert args.master_account == '555555555555'
    assert args.assume_role == 'detectiveAdmin'
    assert args.disabled_regions == 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1'

    args = disableDetective.setup_command_line(['--master_account', '012345678901', '--assume_role', 'detectiveAdmin', '--input_file', 'accounts.csv'])
    assert args.master_account == '012345678901'
    assert args.disabled_regions == None

    args = disableDetective.setup_command_line(['--master_account', '000000000001', '--assume_role', 'detectiveAdmin', '--disabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])
    assert args.master_account == '000000000001'

    # Wrong master account
    # The internal function _master_account_type() should raise argparse.ArgumentTypeError, however this exception gets supressed by argparse, and SystemExit is raised instead.
    with pytest.raises(SystemExit):
    	disableDetective.setup_command_line(['--master_account', '12345', '--assume_role', 'detectiveAdmin', '--disabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])
    
    # Non existent input file and no delete_graph flag
    with pytest.raises(SystemExit):
    	disableDetective.setup_command_line(['--master_account', '000000000001', '--assume_role', 'detectiveAdmin', '--disabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts1.csv'])
    
    # Non existent input file with delete_graph flag provided
    with pytest.raises(SystemExit):
    	disableDetective.setup_command_line(['--master_account', '000000000001', '--assume_role', 'detectiveAdmin', '--disabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts1.csv', '--delete_graph'])
    
    # No input file provided and no delete_graph flag
    with pytest.raises(SystemExit):
        disableDetective.setup_command_line(['--master_account', '000000000001', '--assume_role', 'detectiveAdmin', '--disabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1'])
    
    # No input file provided but delete_graph is set
    args = disableDetective.setup_command_line(['--master_account', '000000000001', '--assume_role', 'detectiveAdmin', '--disabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--delete_graph'])
    assert args.input_file == None
    assert args.delete_graph == True
    
###
# The purpose of this test is to make sure we read accounts and emails correctly from the input .csv file in enableDetective.py
###
def test_read_accounts_csv_enableDetective():
	args = enableDetective.setup_command_line(['--master_account', '555555555555', '--assume_role', 'detectiveAdmin', '--enabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])

	accounts_dict = enableDetective.read_accounts_csv(args.input_file)

	assert len(accounts_dict.keys()) == 6
	assert accounts_dict == {"123456789012":"random@gmail.com", "000012345678":"email@gmail.com", "555555555555":"test5@gmail.com", "111111111111":"test1@gmail.com", "222222222222":"test2@gmail.com", "333333333333":"test3@gmail.com"}

###
# The purpose of this test is to make sure we read accounts and emails correctly from the input .csv file in disableDetective.py
###
def test_read_accounts_csv_disableDetective():
	# a test case where an input file is provided, although some of the lines are not correct
	args = disableDetective.setup_command_line(['--master_account', '555555555555', '--assume_role', 'detectiveAdmin', '--disabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts.csv'])

	accounts_dict = disableDetective.read_accounts_csv(args.input_file)

	assert len(accounts_dict.keys()) == 6
	assert accounts_dict == {"123456789012":"random@gmail.com", "000012345678":"email@gmail.com", "555555555555":"test5@gmail.com", "111111111111":"test1@gmail.com", "222222222222":"test2@gmail.com", "333333333333":"test3@gmail.com"}

	# a test case where no input file is provided
	args = disableDetective.setup_command_line(['--master_account', '555555555555', '--assume_role', 'detectiveAdmin', '--disabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--delete_graph'])
	assert args.input_file == None
	accounts_dict = disableDetective.read_accounts_csv(args.input_file)
	assert accounts_dict == {}

	# a test case where an empty input file is provided, along with delete_graph. This is not an error, although clients should not run with this kind of input
	args = disableDetective.setup_command_line(['--master_account', '555555555555', '--assume_role', 'detectiveAdmin', '--disabled_regions', 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1', '--input_file', 'accounts2.csv', '--delete_graph'])
	accounts_dict = disableDetective.read_accounts_csv(args.input_file)
	assert accounts_dict == {}
	assert args.delete_graph == True

###
# The purpose of this test is to make sure we extract regions correctly in enableDetective.py
###	
def test_get_regions_enableDetective():
	# Regions are provide by user
	regions = enableDetective.get_regions(None, 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1')
	assert regions == ['us-east-1', 'us-east-2', 'us-west-2', 'ap-northeast-1', 'eu-west-1']

	# Need to use Boto to get the regions
	boto_session = Mock()
	boto_session.get_available_regions.return_value = ['us-east-1', 'us-east-2']

	regions = enableDetective.get_regions(boto_session, None)
	assert regions == ['us-east-1', 'us-east-2']


###
# The purpose of this test is to make sure we extract regions correctly in disableDetective.py
### 
def test_get_regions_disableDetective():
	# Regions are provide by user
	regions = disableDetective.get_regions(None, 'us-east-1,us-east-2,us-west-2,ap-northeast-1,eu-west-1')
	assert regions == ['us-east-1', 'us-east-2', 'us-west-2', 'ap-northeast-1', 'eu-west-1']

	# Need to use Boto to get the regions
	boto_session = Mock()
	boto_session.get_available_regions.return_value = ['us-east-1', 'us-east-2']

	regions = disableDetective.get_regions(boto_session, None)
	assert regions == ['us-east-1', 'us-east-2']

###
# The purpose of this test is to make sure get_members() runs correctly in both enableDetective.py and disableDetective.py
### 
def test_get_members_enableDetective_and_disableDetective():
    d_client = Mock()

    # Test case where we have both active and pending accounts
    d_client.list_members.return_value = {"MemberDetails":[{"AccountId":"123456789012", "Status":"ENABLED"}, {"AccountId":"111111111111", "Status":"ENABLED"}, {"AccountId":"222222222222", "Status":"INVITED"}]}

    # Check correctness in enableDetective (with 2 specified graphs)
    all_ac, pending = enableDetective.get_members(d_client, ["graph1", "graph2"])

    assert all_ac == {"graph1": {"123456789012", "111111111111", "222222222222"}, "graph2": {"123456789012", "111111111111", "222222222222"}}
    assert pending == {"graph1": {"222222222222"}, "graph2": {"222222222222"}}

    # Check correctness in disableDetective (with 2 specified graphs)
    all_ac, pending = disableDetective.get_members(d_client, ["graph1", "graph2"])

    assert all_ac == {"graph1": {"123456789012", "111111111111", "222222222222"}, "graph2": {"123456789012", "111111111111", "222222222222"}}
    assert pending == {"graph1": {"222222222222"}, "graph2": {"222222222222"}}

    # Test case with no pending accounts
    d_client.list_members.return_value = {"MemberDetails":[{"AccountId":"111111111111", "Status":"ENABLED"}]}

    # Check correctness in enableDetective (with 1 specified graph)
    all_ac, pending = enableDetective.get_members(d_client, ["graph1"])

    assert all_ac == {"graph1": {"111111111111"}}
    assert pending == {"graph1": set()}

    # Check correctness in disableDetective (with 1 specified graph)
    all_ac, pending = disableDetective.get_members(d_client, ["graph1"])

    assert all_ac == {"graph1": {"111111111111"}}
    assert pending == {"graph1": set()}


def test_create_members():
    d_client = Mock()

    # The existing memebers and new required members don't overlap. Creation causes no errors.
    d_client.create_members.return_value = {'UnprocessedAccounts': {}, 'Members': [{"AccountId": "111111111111"}, {"AccountId": "222222222222"}]}

    created_members = enableDetective.create_members(d_client, "graph1", {"333333333333"}, {"111111111111": "1@gmail.com", "222222222222": "2@gmail.com"})
    assert created_members == {"111111111111", "222222222222"}

    # The existing memebers and new required members overlap by one account. Creation causes no errors.
    d_client.create_members.return_value = {'UnprocessedAccounts': {}, 'Members': [{"AccountId": "111111111111"}]}

    created_members = enableDetective.create_members(d_client, "graph1", {"222222222222"}, {"111111111111": "1@gmail.com", "222222222222": "2@gmail.com"})
    assert created_members == {"111111111111"}

    # All required members already exist. Creation causes no errors.
    d_client.create_members.return_value = {'UnprocessedAccounts': {}, 'Members': []}

    created_members = enableDetective.create_members(d_client, "graph1", {"111111111111", "222222222222", "333333333333"}, {"111111111111": "1@gmail.com", "222222222222": "2@gmail.com"})
    assert created_members == set()


    # The existing memebers and new required members don't overlap. Creation causes 1 error.
    d_client.create_members.return_value = {'UnprocessedAccounts': {"AccountId": "111111111111", "Reason": "some_reason"}, 'Members': [{"AccountId": "222222222222"}]}

    created_members = enableDetective.create_members(d_client, "graph1", {"333333333333"}, {"111111111111": "1@gmail.com", "222222222222": "2@gmail.com"})
    assert created_members == {"222222222222"}

def test_enable_detective():
    d_client = Mock()

    d_client.list_graphs.return_value = {'GraphList': []}
    d_client.create_graph.return_value = {'GraphArn': 'fooGraph123'}

    graphs = enableDetective.enable_detective(d_client, "us-east-2")

    assert graphs == ['fooGraph123']

    





