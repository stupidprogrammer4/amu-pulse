from typing import Annotated

from fastapi import Depends

from src.modules.price.assets.config.constants import (
    ASSET_ID_ENCRYPTION,
    ASSET_SWITCH_ID_ENCRYPTION,
)
from src.web.dependencies import decode_path_id

AssetID = Annotated[int, Depends(decode_path_id(ASSET_ID_ENCRYPTION, "Asset"))]

AssetSwitchID = Annotated[
    int,
    Depends(decode_path_id(ASSET_SWITCH_ID_ENCRYPTION, "AssetSwitch")),
]

AssetIDPath = Annotated[
    int,
    Depends(decode_path_id(ASSET_ID_ENCRYPTION, "Asset", "asset_id")),
]

AssetSwitchIDPath = Annotated[
    int,
    Depends(
        decode_path_id(
            ASSET_SWITCH_ID_ENCRYPTION, "AssetSwitch", "asset_switch_id"
        )
    ),
]
