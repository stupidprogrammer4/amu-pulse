from typing import Annotated

from fastapi import Depends

from src.modules.identity.admins.config.constants import ADMIN_ID_ENCRYPTION
from src.web.dependencies import decode_path_id

AdminID = Annotated[
    int, Depends(decode_path_id(ADMIN_ID_ENCRYPTION, "Admin"))
]

AdminIDPath = Annotated[
    int,
    Depends(decode_path_id(ADMIN_ID_ENCRYPTION, "Admin", "admin_id")),
]
