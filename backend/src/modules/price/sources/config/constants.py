from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from src.common.bases.encryption import IDEncryption

# a prime modulus, so every coefficient is coprime with it. It is kept under
# the 100_000_000 offset step so each module's public ids land in a range of
# their own: sources own [200_000_000, 299_999_988].
SOURCE_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=60_221_407,
    offset=200_000_000,
)

# a foreign key to a source, encoded with the source's own encryption
# wherever it appears in another module's output
SourceIDField = Annotated[
    int, PlainSerializer(SOURCE_ID_ENCRYPTION.encode, return_type=int)
]

# the input side: a client sends the public source id, decoded back to the
# internal one when a DTO parses it (raises 422 on a malformed id)
SourceIDInput = Annotated[int, AfterValidator(SOURCE_ID_ENCRYPTION.decode)]
