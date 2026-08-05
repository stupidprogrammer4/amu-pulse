from typing import Annotated

from fastapi import Depends

from src.modules.price.bubbles.config.constants import BUBBLE_ID_ENCRYPTION
from src.web.dependencies import decode_path_id

# the public bubble id in a route path, decoded to the internal one
BubbleID = Annotated[
    int, Depends(decode_path_id(BUBBLE_ID_ENCRYPTION, "Bubble"))
]
