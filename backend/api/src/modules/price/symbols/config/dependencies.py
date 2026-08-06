from typing import Annotated

from fastapi import Depends

from src.modules.price.symbols.config.constants import SYMBOL_ID_ENCRYPTION
from src.web.dependencies import decode_path_id

SymbolID = Annotated[
    int, Depends(decode_path_id(SYMBOL_ID_ENCRYPTION, "Symbol"))
]

SymbolIDPath = Annotated[
    int,
    Depends(decode_path_id(SYMBOL_ID_ENCRYPTION, "Symbol", "symbol_id")),
]
