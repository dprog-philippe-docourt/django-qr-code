from datetime import datetime
from typing import Optional, Union

QR_CODE_GENERATION_VERSION_DATE: datetime = datetime(year=2020, month=9, day=8, hour=12)
SIZE_DICT: dict = {'t': 6, 's': 12, 'm': 18, 'l': 30, 'h': 48}
ERROR_CORRECTION_DICT: dict = {'L': 'l', 'M': 'm', 'Q': 'q', 'H': 'h'}
DEFAULT_MODULE_SIZE: Union[str, int] = 'm'
DEFAULT_BORDER_SIZE: int = 4
DEFAULT_VERSION: Optional[int] = None
DEFAULT_IMAGE_FORMAT: str = 'svg'
DEFAULT_ERROR_CORRECTION: str = 'm'
DEFAULT_ECI: bool = False
DEFAULT_CACHE_ENABLED: bool = True
DEFAULT_URL_SIGNATURE_ENABLED: bool = True

ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER: str = 'ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER'
SIGNING_KEY: str = 'SIGNING_KEY'
TOKEN_LENGTH: str = 'TOKEN_LENGTH'
SIGNING_SALT: str = 'SIGNING_SALT'
