from typing import Annotated

from pydantic import AfterValidator, PlainSerializer

from src.common.bases.encryption import IDEncryption

# the symbols own the 500M step, so each module keeps its own range
SYMBOL_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=14_142_135,
    offset=500_000_000,
)

# a foreign key to a symbol, encoded wherever another module returns it
SymbolIDField = Annotated[
    int, PlainSerializer(SYMBOL_ID_ENCRYPTION.encode, return_type=int)
]

# the input side: a public id a DTO decodes back, 422 on a malformed one
SymbolIDInput = Annotated[int, AfterValidator(SYMBOL_ID_ENCRYPTION.decode)]
