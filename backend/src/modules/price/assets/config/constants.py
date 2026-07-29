from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from src.common.bases.encryption import IDEncryption

# prime modulus under the 100M offset step, so each module owns a range
ASSET_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=31_415_926,
    offset=100_000_000,
)

# a foreign key to an asset, encoded wherever another module returns it
AssetIDField = Annotated[
    int, PlainSerializer(ASSET_ID_ENCRYPTION.encode, return_type=int)
]

# the input side: a public id a DTO decodes back, 422 on a malformed one
AssetIDInput = Annotated[int, AfterValidator(ASSET_ID_ENCRYPTION.decode)]
