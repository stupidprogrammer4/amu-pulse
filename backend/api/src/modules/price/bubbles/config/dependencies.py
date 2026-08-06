from typing import Annotated

from fastapi import Depends

from src.modules.price.bubbles.config.constants import BUBBLE_ID_ENCRYPTION
from src.web.dependencies import decode_path_id

BubbleID = Annotated[
    int, Depends(decode_path_id(BUBBLE_ID_ENCRYPTION, "Bubble"))
]
