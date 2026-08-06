from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from src.common.bases.encryption import IDEncryption

SOURCE_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=60_221_407,
    offset=200_000_000,
)

SourceIDField = Annotated[
    int, PlainSerializer(SOURCE_ID_ENCRYPTION.encode, return_type=int)
]

SourceIDInput = Annotated[int, AfterValidator(SOURCE_ID_ENCRYPTION.decode)]
