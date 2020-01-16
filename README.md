# amazon-detective-multiaccount-scripts

## About these scripts

These scripts automate the the following processes:

* Enabling Detective for a master account
* Adding member accounts to the master account's behavior graph
* Removing member accounts from a master account's behavior graph
* Disabling Detective for a master account

The scripts act across a group of AWS accounts that are in your control.

**enableDetective.py** does the following:

1. Enables Detective, if the master account does not already have Detective enabled
2. Sends invitations from the master account to the specified member accounts
3. Accepts invitations for all member accounts

The result is a master account that contains all security findings for all member accounts.

Because Detective is regionally isolated, findings for each member account roll up to the corresponding Region in the master account. For example, the us-east-1 Region in your Detective master account monitors the security findings for all of the us-east-1 findings from all of the associated member accounts.

**Note:** Account owners of member accounts receive an email for each Region requesting that they accept the invitation to link their accounts. Because the script accepts the invitation on their behalf, member accounts can ignore these emails.

**disableDetective.py** does the following:

1. Removes the listed member accounts from the behavior graphs for the master account. 
2. Can optionally disable Detective for the master account.

## Prerequisites

### Role

The scripts depend on a pre-existing role in the master account and all of the member accounts that will be linked.

The role name must be the same in all accounts.

The role trust relationship must allow your instance or local credentials to assume the role.

The AmazonDetectiveFullAccess managed policy shown below contains the permissions that are required for the script to succeed:

#### Role policy

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
                "detective:AcceptInvitation"
            ],
            "Resource": "*"
        }
    ]
}
```

#### Role trust relationship

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

### .csv list of member accounts

A .csv file that provides the list of accounts to be linked to the master account.

Accounts are listed one per line in the format AccountId,EmailAddress.

The EmailAddress must be the email address associated with the root account.

### Account ID of the master account

The account ID of the master account. The master account receives findings for all the linked accounts in the .csv file.

## Setting up the execution environment

### Option 1: Launch an EC2 instance

1. Launch an EC2 instance in your master account <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html>
2. Attach to an instance an IAM role that has permissions to allow the instance to call AssumeRole within the master account.
If you used the EnableDetective.yaml template, then an instance role with a profile name of "EnableDetective" was created.
Otherwise see the documentation on creating an instance role here: <https://aws.amazon.com/blogs/security/easily-replace-or-attach-an-iam-role-to-an-existing-ec2-instance-by-using-the-ec2-console/>.
3. Install the required software
   * APT: sudo apt-get -y install python2-pip python2 git
     * RPM: sudo yum -y install python2-pip python2 git
     * sudo pip install boto3
4. Clone the Repository
   * git clone <https://github.com/aws-samples/amazon-detective-multiaccount-scripts.git>
5. Copy the .csv file containing the account number and email addresses to the instance using one of the following methods:

* S3 `s3 cp s3://bucket/key_name enable.csv .`
  * pscp.exe `pscp local_file_path username@hostname:.`
  * scp `scp local_file_path username@hostname:.`

### Option 2: Run the scripts locally

1. Ensure you have set up on your local machine credentials for your master account that have permission to call AssumeRole.
2. Install the required software:
   * Windows:
     1. Install Python <https://www.python.org/downloads/windows/>
     2. Open command prompt:
        1. pip install boto3
     3. Download sourcecode from <https://github.com/aws-samples/amazon-detective-multiaccount-scripts>
     4. Change directory of command prompt to the newly downloaded amazon-detective-multiaccount-scripts folder
   * Mac:
     1. Install Python <https://www.python.org/downloads/mac-osx/>
     2. Open command prompt:
        1. pip install boto3
     3. Download sourcecode from <https://github.com/aws-samples/amazon-detective-multiaccount-scripts>
     4. Change directory of command prompt to the newly downloaded amazon-detective-multiaccount-scripts folder
   * Linux:
     1. sudo apt-get -y install install python2-pip python2 git
        1. sudo pip install boto3
        2. git clone <https://github.com/aws-samples/amazon-detective-multiaccount-scripts>
     2. cd amazon-detective-multiaccount-scripts
        1. sudo yum install git python
     3. sudo pip install boto3
        1. git clone <https://github.com/aws-samples/amazon-detective-multiaccount-scripts>
     4. cd amazon-detective-multiaccount-scripts

## Executing the scripts

### Enabling Detective

Copy the required .csv file to the same directory as the python script. The file contains a single entry per line, in the format "AccountId,EmailAddress".

```html
usage: enableDetective.py [-h] --master_account MASTER_ACCOUNT --assume_role
                          ASSUME_ROLE
                          input_file

Link AWS accounts as member accounts to a Detective master account

positional arguments:
  input_file            Path to the .csv file containing the list of account IDs
                        and email addresses of the member accounts to link to the master account

arguments:
  -h, --help            Show this help message and exit
  --master_account MASTER_ACCOUNT
                        AWS account ID for the master account
  --assume_role ASSUME_ROLE
                        Role name to assume in each account
  
```

### Disabling Detective

Copy the required .csv file to the same directory as the python script. The file contains a single entry per line, in the format "AccountId,EmailAddress,..."

```html
usage: disabledetective.py [-h] --master_account MASTER_ACCOUNT --assume_role
                           ASSUME_ROLE [--delete_master]
                           input_file

Link AWS accounts to central Detective Account

positional arguments:
  input_file            Path to the .csv file containing the list of account IDs
                        and email addresses

arguments:
  -h, --help            Show this help message and exit
  --master_account MASTER_ACCOUNT
                        Account ID for the master account
  --assume_role ASSUME_ROLE
                        Role name to assume in each account
  --delete_master       Delete the master account. This disables Detective for the master account and deletes the entire behavior graph. If this flag is not included, then the script only deletes from the behavior graph the member accounts listed in the file.
```
