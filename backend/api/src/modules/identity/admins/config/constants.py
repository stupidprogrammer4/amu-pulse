from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from src.common.bases.encryption import IDEncryption

# the admins own the 600M step, so each module keeps its own range
ADMIN_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=17_320_508,
    offset=600_000_000,
)

# a foreign key to an admin, encoded wherever another module returns it
AdminIDField = Annotated[
    int, PlainSerializer(ADMIN_ID_ENCRYPTION.encode, return_type=int)
]

# the input side: a public id a DTO decodes back, 422 on a malformed one
AdminIDInput = Annotated[int, AfterValidator(ADMIN_ID_ENCRYPTION.decode)]
