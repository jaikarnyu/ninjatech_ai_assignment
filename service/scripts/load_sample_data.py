import sys

# Add the path to the directory where your custom modules are located
sys.path.append("/app/")

from service.models.projects import Projects, db, DataValidationError
from service.models.device_firmware_events import DeviceFirmwareEvents
from service.models.device_api_keys import DeviceApiKeys
from service.models.devices import Devices
from service.models.project_membership_api_keys import ProjectMembershipApiKeys
from service.models.project_memberships import ProjectMemberships

# Setup initial projects, memberships, devices, device api keys
print("Creating api keys")
project = Projects(name="Test Project")
project.create()

project_membership = ProjectMemberships(
    project_id=project.id,
    email="test@email.com",
)
project_membership.create()

device = Devices(
    project_id=project.id,
    name="Test Device",
)
device.create()

device_api_key = DeviceApiKeys(
    device_id=device.id,
)
device_api_key.create()

project_membership_api_key = ProjectMembershipApiKeys(
    project_membership_id=project_membership.id,
)
project_membership_api_key.create()

print("-------------------------------------------------")

print("Device api key: %s", device_api_key.secret)
print("Project membership api key: %s", project_membership_api_key.secret)
print("Device id : %s ", device.id)
