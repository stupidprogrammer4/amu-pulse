from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from src.common.bases.encryption import IDEncryption

# a prime modulus, so every coefficient is coprime with it; the offset puts
# the public ids of each module in a range of their own
ASSET_ID_ENCRYPTION = IDEncryption(
    mod=999_999_937,
    coff=314_159_263,
    offset=100_000_000,
)

# a foreign key to an asset, encoded with the asset's own encryption
# wherever it appears in another module's output
AssetIDField = Annotated[
    int, PlainSerializer(ASSET_ID_ENCRYPTION.encode, return_type=int)
]

# the input side: a client sends the public asset id, decoded back to the
# internal one when a DTO parses it (raises 422 on a malformed id)
AssetIDInput = Annotated[int, AfterValidator(ASSET_ID_ENCRYPTION.decode)]
