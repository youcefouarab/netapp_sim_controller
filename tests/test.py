from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from keystoneauth1.session import Session
from keystoneauth1.identity.v3 import Password
from gnocchiclient.client import Client

from context import *


if not OS_VERIFY_CERT:
    disable_warnings(InsecureRequestWarning)
client = Client(1, Session(Password(auth_url=OS_URL + ':' + OS_AUTH_PORT,
                                    username=OS_USERNAME, password=OS_PASSWORD,
                                    user_domain_id=OS_USER_DOMAIN_ID,
                                    project_id=OS_PROJECT_ID),
                           verify=OS_VERIFY_CERT))


for measure in client.metric.get_measures('loss_rate',
                                          resource_id='0000000000000001->0000000000000002'):
    print(measure[0].strftime('%m/%d/%Y, %H:%M:%S  '),
          round(measure[2] * 100, 2), '%')
