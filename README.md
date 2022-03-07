# CloudFormation Drift Remediation

## Installation
This package is available on pypi, you can for example use on of these commands (pipx is recommended)
```shell
pipx install cfn-drift-remediation
pip install cfn-drift-remediation
```

## Usage
1. Run drift detection on a stack, and verify that you want to remediate it by changing the provisioned resource (using the stack as the source of truth).
2. run one of the commands below
3. Run drift detection again to verify that everything is in sync again.

```shell
# Default usage
cfn-drift-remediation stack_name
# Using a different profile
AWS_DEFAULT_PROFILE=profile-name cfn-drift-remediation stack_name
# Using a third party tool like aws-vault
aws-vault exec profile-name -- cfn-drift-remediation stack_name
```

## How this works
This tool will read the existing drift of a stack, iterate through the drifted resources and construct a patch document to change the actual (detected) property values to the expected (stack) values.

## Caveats
- Changes are done with CloudControl API. This does mean that if the drifted resources do not support Cloud Control API, they will be skipped.
- For some resources the order in a list does not matter, this might lead to a failure to apply changes, because Cloud Control API will assume the resource is not in the drifted state it expects.
- We do not support creating resources that were completely deleted from the stack. The drift detection api does not return enough information to construct the replacement resource.

## Development
We use poetry to manage this project

1. Clone this repository
2. Run `poetry install`
3. Activate the virtualenvironment with `poetry shell` (you can also use `poetry run $command`)

### Releasing a new version to pypi
1. Edit pyproject.toml to update the version number
2. Edit cfn_drift_remediation/__init_.py to update the version number
3. Commit the version number bump
4. Run tests `poetry run pytest ` (you might have to install dependencies with `poetry install --dev`)
5. Tag the commit with the version number `git tag x.y.z`
6. Push to GitHub, this will create a new release in pypi and GitHub


### Using poetry in Visual Studio Code
If you want to use poetry in Visual Studio Code, it works best if the virtual environment is created inside the project folder. Once the virtual environment is created, you can run the "Python: Select interpreter" command in Visual Studio Code, and point to the `.venv` folder.


```shell
poetry config virtualenvs.in-project true
```
If you already created the virtual environment, you have to recreate it
```shell
# from within the project folder
poetry env remove $(poetry env list)
poetry install
```
