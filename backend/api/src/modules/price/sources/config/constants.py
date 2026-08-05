from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from src.common.bases.encryption import IDEncryption

# prime modulus under the 100M offset step, so each module owns a range
SOURCE_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=60_221_407,
    offset=200_000_000,
)

# a foreign key to a source, encoded wherever another module returns it
SourceIDField = Annotated[
    int, PlainSerializer(SOURCE_ID_ENCRYPTION.encode, return_type=int)
]

# the input side: a public id a DTO decodes back, 422 on a malformed one
SourceIDInput = Annotated[int, AfterValidator(SOURCE_ID_ENCRYPTION.decode)]
