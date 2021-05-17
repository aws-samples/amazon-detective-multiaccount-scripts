# amazon-detective-multiaccount-scripts

Amazon Detective provides a set of open-source Python scripts in this repository. The scripts require Python 3.

You can use these to perform the following tasks:
* Enable Detective for an administrator account across Regions. When you enable Detective, you can assign tag values to the behavior graph.
* Add member accounts to an administrator account's behavior graphs across Regions.
* Optionally send invitation emails to the member accounts. You can also configure the request to not send invitation emails.
* Remove member accounts from an administrator account's behavior graphs across Regions.
* Disable Detective for an administrator account across Regions. When an administrator account disables Detective, the administrator account's behavior graph in each Region is disabled.

For more information on how to use these scripts, see [Using the Amazon Detective Python scripts](https://docs.aws.amazon.com/detective/latest/adminguide/detective-github-scripts.html)

## Contributing to this project

### Running tests

```
# Install requirements
pip3 install boto3 pytest

# In the tests/ directory...
pytest -s
```
