from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from src.common.bases.encryption import IDEncryption

ADMIN_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=17_320_508,
    offset=600_000_000,
)

AdminIDField = Annotated[
    int, PlainSerializer(ADMIN_ID_ENCRYPTION.encode, return_type=int)
]

AdminIDInput = Annotated[int, AfterValidator(ADMIN_ID_ENCRYPTION.decode)]
