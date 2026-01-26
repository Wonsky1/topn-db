"""
Pydantic schemas for the application.
"""

from .cities import (
    CityBase,
    CityCreate,
    CityList,
    CityResponse,
    CityUpdate,
    CityWithDistrictsResponse,
)
from .districts import (
    DistrictBase,
    DistrictCreate,
    DistrictList,
    DistrictResponse,
    DistrictUpdate,
    DistrictWithCityResponse,
)
from .items import (
    ItemRecordBase,
    ItemRecordCreate,
    ItemRecordList,
    ItemRecordResponse,
    ItemsToSendResponse,
)
from .tasks import (
    MonitoringTaskBase,
    MonitoringTaskCreate,
    MonitoringTaskList,
    MonitoringTaskResponse,
    MonitoringTaskUpdate,
    MonitoringTaskWithRelationsResponse,
)
