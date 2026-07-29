from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from src.common.bases.encryption import IDEncryption

# a prime modulus, so every coefficient is coprime with it. It is kept under
# the 100_000_000 offset step so each module's public ids land in a range of
# their own: bubbles own [300_000_000, 399_999_988].
BUBBLE_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=27_182_818,
    offset=300_000_000,
)

# a foreign key to a bubble, encoded wherever another module returns it
BubbleIDField = Annotated[
    int, PlainSerializer(BUBBLE_ID_ENCRYPTION.encode, return_type=int)
]

# the input side: a public id a DTO decodes back, 422 on a malformed one
BubbleIDInput = Annotated[int, AfterValidator(BUBBLE_ID_ENCRYPTION.decode)]
