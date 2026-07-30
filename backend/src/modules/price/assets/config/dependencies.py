from typing import Annotated

from fastapi import Depends

from src.modules.price.assets.config.constants import (
    ASSET_ID_ENCRYPTION,
    ASSET_SWITCH_ID_ENCRYPTION,
)
from src.web.dependencies import decode_path_id

# the public asset id in a route path, decoded to the internal one
AssetID = Annotated[int, Depends(decode_path_id(ASSET_ID_ENCRYPTION, "Asset"))]

# the public id of one row of an asset's pricing order
AssetSwitchID = Annotated[
    int,
    Depends(decode_path_id(ASSET_SWITCH_ID_ENCRYPTION, "AssetSwitch")),
]
