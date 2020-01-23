# amazon-detective-multiaccount-scripts

## About these scripts

These scripts automate the the following processes:

* Enabling Detective for a master account across Regions
* Adding member accounts to the master account's behavior graph across Regions
* Removing member accounts from a master account's behavior graph across Regions
* Disabling Detective for a master account across Regions. Disabling Detective deletes the master account's behavior graph in each Region.

The scripts act across a group of AWS accounts that are in your control.

**enableDetective.py** does the following:

1. Enables Detective in for a master account in each specified Region, if the master account does not already have Detective enabled in that Region.
2. Sends invitations from the master account to the specified member accounts for each behavior graph.
3. Automatically accepts the invitations for the member accounts. Because the script accepts the invitation on their behalf, member accounts can ignore these emails.

The result is a master account that monitors security findings for all member accounts.

Detective is regionally isolated. Findings for each member account are ingested into the master account's behavior graph for the corresponding Region. For example, the master account's behavior graph in the us-east-1 Region receives security findings from the us-east-1 Region from the associated member accounts.


**disableDetective.py** deletes the specified member accounts from the master account's behavior graphs across the specified Regions.

It also provides an option to disable Detective for the master account across the specified Regions.


## Required permissions for the script

The scripts require a pre-existing role in the master account and all of the member accounts that you add or remove.

The role name must be the same in all accounts.

The role trust relationship must allow your instance or local credentials to assume the role.

The AmazonDetectiveFullAccess managed policy shown below contains the permissions that are required for the script to succeed:

### Role policy

```json
 {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "detective:CreateMembers",
                "detective:DeleteMembers",
                "detective:AcceptInvitation",
                "detective:ListGraphs",
                "detective:ListMembers"
            ],
            "Resource": "*"
        }
    ]
}
```

### Role trust relationship

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::<ACCOUNTID>:user/<USERNAME>"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

If you do not have a common role that includes at least the above permissions, you must create a role with at least those permissions in each member account and in the master account.

When you create the role, make sure that you do the following:

* Use the same role name in every account
* Select the AmazonDetectiveFullAccess managed policy

To automate this process, you can use the **EnableDetective.yaml** CloudFormation Template. Because the template creates only global resources, it can be created in any Region.


## Setting up the execution environment

You can run the scripts from either an EC2 instance or from a local machine.

### Option 1: Launch an EC2 instance

1. Launch an EC2 instance in your master account <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html>
2. Attach to an instance an IAM role that has permissions to allow the instance to call AssumeRole within the master account.
If you used the EnableDetective.yaml template, then an instance role with a profile name of "EnableDetective" was created.
Otherwise see the documentation on creating an instance role here: <https://aws.amazon.com/blogs/security/easily-replace-or-attach-an-iam-role-to-an-existing-ec2-instance-by-using-the-ec2-console/>.
3. Install the required software
   * APT: sudo apt-get -y install python3-pip python3 git
   * RPM: sudo yum -y install python3-pip python3 git
   * sudo pip install boto3
4. Clone the Repository
   * git clone <https://github.com/aws-samples/amazon-detective-multiaccount-scripts.git>

### Option 2: Run the scripts locally

1. Ensure you have set up on your local machine credentials for your master account that have permission to call AssumeRole.
2. Install the required software:
   * Windows:
     1. Install Python <https://www.python.org/downloads/windows/>
     2. Open command prompt:
        1. pip install boto3
     3. Download sourcecode from <https://github.com/aws-samples/amazon-detective-multiaccount-scripts>
   * Mac:
     1. Install Python <https://www.python.org/downloads/mac-osx/>
     2. Open command prompt:
        1. pip install boto3
     3. Download sourcecode from <https://github.com/aws-samples/amazon-detective-multiaccount-scripts>
   * Linux:
     1. sudo apt-get -y install install python3-pip python3 git
        1. sudo pip install boto3
        2. git clone <https://github.com/aws-samples/amazon-detective-multiaccount-scripts>
     2. cd amazon-detective-multiaccount-scripts
        1. sudo yum install git python
     3. sudo pip install boto3
        1. git clone <https://github.com/aws-samples/amazon-detective-multiaccount-scripts>

## Creating a .csv list of member accounts to add or remove

To identify the member accounts to add to or remove from the behavior graphs, you provide a .csv file that contains the list of accounts.

Each account is listed on a separate line. Each member account entry contains the AWS account ID and the account's root user email address.

Example:

```
111122223333,srodriguez@example.com
444455556666,rroe@example.com
```


## Executing the scripts

### Running enableDetective.py

1. Copy the .csv file containing the account number and email addresses to the **amazon-detective-multi-account-scripts** directory on your EC2 instance or local machine.
If you are running the scripts from an EC2 instance, use one of the following methods:
  * S3 `s3 cp s3://bucket/key_name enable.csv .`
  * pscp.exe `pscp local_file_path username@hostname:.`
  * scp `scp local_file_path username@hostname:.`
2. Change to the **amazon-detective-multiaccount-scripts** directory.
3. Run the enableDetective.py script.


```html
usage: enableDetective.py [-h] --master_account MASTER_ACCOUNT --assume_role
                          ASSUME_ROLE --enabled_regions REGION_LIST
                          input_file

Adds member accounts to the master account's behavior graph in each Region.

positional arguments:
  input_file            Path to the .csv file containing the list of account IDs
                        and email addresses of the member accounts to add to the master account's behavior graph in each Region

arguments:
  -h, --help            Show a help message and exits
  --master_account MASTER_ACCOUNT
                        AWS account ID for the master account
  --assume_role ASSUME_ROLE
                        Role name to assume in each account
  --enabled_regions REGION_LIST
                        Optional Comma-separated list of Regions in which to enable Detective for the master account and add the member
                        accounts to the behavior graph. If the master account already has a behavior graph in a Region, then 
                        the member accounts are added to that behavior graph. If you do not provide a list of Regions, then
                        the script acts across all Regions that Detective supports.
  
```
  


### Running disableDetective.py

1. Copy the .csv file containing the account number and email addresses to the **amazon-detective-multi-account-scripts** directory on your EC2 instance or local machine.
If you are running the scripts from an EC2 instance, use one of the following methods:
  * S3 `s3 cp s3://bucket/key_name enable.csv .`
  * pscp.exe `pscp local_file_path username@hostname:.`
  * scp `scp local_file_path username@hostname:.`
2. Change to the **amazon-detective-multiaccount-scripts** directory.

```html
usage: disabledetective.py [-h] --master_account MASTER_ACCOUNT --assume_role
                           ASSUME_ROLE  --disabled_regions REGION_LIST [--delete_master]
                           input_file

Removes member accounts from the master account's behavior graph in each Region.

positional arguments:
  input_file            Name of the .csv file containing the list of account IDs
                        and email addresses

arguments:
  -h, --help            Show a help message and exits
  --master_account MASTER_ACCOUNT
                        Account ID for the master account
  --assume_role ASSUME_ROLE
                        Role name to assume in each account
  --disabled_regions REGION_LIST
                        Optional. Comma-separated list of Regions from which to remove the member accounts from the master account's
                        behavior graph.  If you do not provide a list of Regions, then the script acts across all Regions that 
                        Detective supports.
  --delete_master       If this flag is included, then instead of only deleting the member accounts from the master account's 
                        behavior graphs, the script disables Detective for the master account in all of the specified Regions.
                        When Detective is disabled for a master account, the master account's behavior graph is disabled.
```
