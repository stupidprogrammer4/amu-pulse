from typing import Annotated

from fastapi import Depends

from src.modules.identity.admins.config.constants import ADMIN_ID_ENCRYPTION
from src.web.dependencies import decode_path_id

# the public admin id in a route path, decoded to the internal one
AdminID = Annotated[
    int, Depends(decode_path_id(ADMIN_ID_ENCRYPTION, "Admin"))
]

# the same id, where the path names it after the admin itself
AdminIDPath = Annotated[
    int,
    Depends(decode_path_id(ADMIN_ID_ENCRYPTION, "Admin", "admin_id")),
]
