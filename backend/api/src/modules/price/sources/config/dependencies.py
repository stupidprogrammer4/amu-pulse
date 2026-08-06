from typing import Annotated

from fastapi import Depends

from src.modules.price.sources.config.constants import SOURCE_ID_ENCRYPTION
from src.web.dependencies import decode_path_id

SourceID = Annotated[
    int, Depends(decode_path_id(SOURCE_ID_ENCRYPTION, "Source"))
]

SourceIDPath = Annotated[
    int,
    Depends(decode_path_id(SOURCE_ID_ENCRYPTION, "Source", "source_id")),
]
