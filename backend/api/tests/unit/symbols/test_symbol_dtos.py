import pytest
from pydantic import ValidationError

from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.symbols.domain.dtos import SymbolCreate, SymbolUpdate
from src.modules.price.symbols.domain.enums import CurrencyType, SymbolCode


def _create(**over: object) -> SymbolCreate:
    data = {
        "title": "هر گرم طلای ۱۸ عیار",
        "code": SymbolCode.GOLD18_GRAM,
        "asset_id": ASSET_ID_ENCRYPTION.encode(1),
        "currency": CurrencyType.RIAL,
        "primary_color": "#c8a44b",
    }
    data.update(over)
    return SymbolCreate(**data)  # type: ignore[arg-type]


class TestAssetID:
    def test_a_public_asset_id_is_decoded(self) -> None:
        data = _create()

        assert data.asset_id == 1

    def test_an_id_outside_the_asset_range_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _create(asset_id=42)


class TestFields:
    def test_a_world_line_is_quoted_in_dollars(self) -> None:
        data = _create(
            code=SymbolCode.XAU_OUNCE,
            currency=CurrencyType.USD,
        )

        assert data.currency is CurrencyType.USD

    def test_the_description_is_optional(self) -> None:
        data = _create()

        assert data.description is None

    def test_an_unknown_code_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _create(code="gold24_gram")

    def test_an_unknown_currency_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _create(currency="euro")


class TestUpdate:
    def test_a_patch_may_carry_one_field(self) -> None:
        patch = SymbolUpdate(title="مظنه")

        assert patch.to_row() == {"title": "مظنه"}

    def test_the_code_is_not_patchable(self) -> None:
        patch = SymbolUpdate(title="مظنه")

        assert "code" not in patch.to_row(exclude_unset=False)

    def test_an_unknown_currency_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SymbolUpdate(currency="euro")  # type: ignore[arg-type]
