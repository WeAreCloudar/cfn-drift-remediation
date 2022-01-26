from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile
from pathlib import Path
from os.path import dirname

DOWNLOAD_URL_TEMPLATE = "https://schema.cloudformation.{region}.amazonaws.com/CloudformationSchema.zip"
# TODO: Is this the right folder to save that data
# TODO: should we update in github instead with a github action?
CFN_SCHEMA_FOLDER = Path(dirname(__file__)) / "cloudformation_resource_schemas"


def get_schemas(force_update=False, region='us-east-1'):
    download_url = DOWNLOAD_URL_TEMPLATE.format(region=region)
    CFN_SCHEMA_FOLDER.mkdir(exist_ok=True)
    # TODO: be smarter about updates (eg check on age)
    if next(CFN_SCHEMA_FOLDER.iterdir(), None) and not force_update:
        return
    with urlopen(download_url) as resp:
        zipfile = ZipFile(BytesIO(resp.read()))
    zipfile.extractall(CFN_SCHEMA_FOLDER)
