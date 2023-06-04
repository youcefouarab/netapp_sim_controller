from os import getenv

from keystoneauth1.session import Session
from keystoneauth1.identity.v3 import Password
from gnocchiclient.client import Client

from context import config


OS_URL = getenv('OPENSTACK_URL', '')
OS_AUTH_PORT = getenv('OPENSTACK_AUTH_PORT', '')
OS_GNOCCHI_PORT = getenv('OPENSTACK_GNOCCHI_PORT', '')
OS_USERNAME = getenv('OPENSTACK_USERNAME', '')
OS_PASSWORD = getenv('OPENSTACK_PASSWORD', '')
OS_USER_DOMAIN_ID = getenv('OPENSTACK_USER_DOMAIN_ID', '')
OS_USER_ID = getenv('OPENSTACK_USER_ID', '')
OS_PROJECT_ID = getenv('OPENSTACK_PROJECT_ID', '')
OS_ARCHIVE_POLICY = getenv('OPENSTACK_ARCHIVE_POLICY', '')

_client = None


def _os_authenticate():
    return Session(Password(auth_url=OS_URL + ':' + OS_AUTH_PORT,
                            username=OS_USERNAME, password=OS_PASSWORD,
                            user_domain_id=OS_USER_DOMAIN_ID,
                            project_id=OS_PROJECT_ID))


def _os_gnocchi_client():
    # 'singleton' gnocchi client
    global _client
    if not _client:
        _client = Client(1, _os_authenticate())
    return _client


client = _os_gnocchi_client()

for measure in client.metric.get_measures('delay',
                                          resource_id='0000000000000001->0000000000000002'):
    print(measure[0].strftime('%m/%d/%Y, %H:%M:%S  '),
          round(measure[2] * 1000, 2))
