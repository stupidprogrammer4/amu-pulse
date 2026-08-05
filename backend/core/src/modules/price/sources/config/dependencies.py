from typing import Annotated

from fastapi import Depends

from src.modules.price.sources.config.constants import SOURCE_ID_ENCRYPTION
from src.web.dependencies import decode_path_id

# the public source id in a route path, decoded to the internal one
SourceID = Annotated[
    int, Depends(decode_path_id(SOURCE_ID_ENCRYPTION, "Source"))
]

# the same id, where the path names it after the source itself
SourceIDPath = Annotated[
    int,
    Depends(decode_path_id(SOURCE_ID_ENCRYPTION, "Source", "source_id")),
]
