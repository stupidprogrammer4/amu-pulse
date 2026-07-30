from datetime import datetime

import pytest

from src.common.errors.exceptions import NotFoundException
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.symbols.config.constants import SYMBOL_ID_ENCRYPTION
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode
from src.modules.price.symbols.domain.schemas import SymbolOut
from src.web.dependencies import decode_path_id


def _symbol_out(id: int) -> SymbolOut:
    """
    Desc: Build a SymbolOut carrying the given internal id.
    Args:
        id (int): The internal id.
    Returns:
        return (SymbolOut): The output schema.
    """
    now = datetime(2026, 7, 30, 12, 0, 0)
    return SymbolOut(
        id=id,
        title="هر گرم طلای ۱۸ عیار",
        code=SymbolCode.GOLD18_GRAM,
        asset_id=1,
        currency=CurrencyType.RIAL,
        description=None,
        created_at=now,
        updated_at=now,
    )


class TestRoundTrip:
    @pytest.mark.parametrize("id", [1, 2, 999, 1_000_000, 99_999_988])
    def test_an_encoded_id_decodes_back(self, id: int) -> None:
        public = SYMBOL_ID_ENCRYPTION.encode(id)

        assert SYMBOL_ID_ENCRYPTION.decode(public) == id

    def test_the_public_id_sits_in_the_500m_step(self) -> None:
        public = SYMBOL_ID_ENCRYPTION.encode(1)

        assert 500_000_000 <= public < 600_000_000

    def test_it_does_not_collide_with_the_asset_range(self) -> None:
        # every module owns a step, so a pasted id addresses one table only
        symbol = SYMBOL_ID_ENCRYPTION.encode(1)

        with pytest.raises(Exception):
            ASSET_ID_ENCRYPTION.decode(symbol)


class TestOutput:
    def test_only_the_wire_id_is_encoded(self) -> None:
        out = _symbol_out(7)

        assert out.id == 7
        assert out.model_dump()["id"] == SYMBOL_ID_ENCRYPTION.encode(7)

    def test_the_asset_id_is_encoded_too(self) -> None:
        out = _symbol_out(7)

        assert out.model_dump()["asset_id"] == ASSET_ID_ENCRYPTION.encode(1)


class TestPathDependency:
    def test_it_decodes_a_public_id(self) -> None:
        decode = decode_path_id(SYMBOL_ID_ENCRYPTION, "Symbol")
        public = SYMBOL_ID_ENCRYPTION.encode(12)

        assert decode(id=public) == 12

    def test_a_malformed_id_is_not_found(self) -> None:
        decode = decode_path_id(SYMBOL_ID_ENCRYPTION, "Symbol")

        with pytest.raises(NotFoundException):
            decode(id=42)
