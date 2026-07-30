from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from src.common.bases.encryption import IDEncryption
from src.modules.price.assets.domain.enums import AssetCode

# prime modulus under the 100M offset step, so each module owns a range
ASSET_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=31_415_926,
    offset=100_000_000,
)

# the pricing-order rows own the 400M step
ASSET_SWITCH_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=16_180_339,
    offset=400_000_000,
)

# a foreign key to an asset, encoded wherever another module returns it
AssetIDField = Annotated[
    int, PlainSerializer(ASSET_ID_ENCRYPTION.encode, return_type=int)
]

# the input side: a public id a DTO decodes back, 422 on a malformed one
AssetIDInput = Annotated[int, AfterValidator(ASSET_ID_ENCRYPTION.decode)]


# what a carat means as a fraction; an asset absent here is not a metal
# and cannot be priced off a world spot quote
ASSET_PURITY: dict[AssetCode, Decimal] = {
    AssetCode.GOLD18: Decimal(18) / Decimal(24),
}

# the input side of a pricing-order row's public id
AssetSwitchIDInput = Annotated[
    int, AfterValidator(ASSET_SWITCH_ID_ENCRYPTION.decode)
]
