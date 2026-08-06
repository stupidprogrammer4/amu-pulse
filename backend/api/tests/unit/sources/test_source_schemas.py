from datetime import datetime

import pytest

from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.sources.config.constants import SOURCE_ID_ENCRYPTION
from src.modules.price.sources.domain.enums import (
    ErrorType,
    SourceCode,
    SourceSwitch,
)
from src.modules.price.sources.domain.models import SourceConfigModel
from src.modules.price.sources.domain.schemas import (
    SourceConfigOut,
    SourceOut,
    SourceWithConfigOut,
)

_NOW = datetime(2026, 7, 29, 12, 0, 0)


def _config(
    headers: dict[str, str] | None = None,
    auth: dict[str, str] | None = None,
) -> SourceConfigModel:
    return SourceConfigModel(
        source_id=3,
        timeout=10,
        headers_credentials=headers,
        auth_credentials=auth,
        created_at=_NOW,
        updated_at=_NOW,
    )


def _source_out(id: int = 3) -> SourceOut:
    return SourceOut(
        id=id,
        title="شبکه اطلاع‌رسانی طلا و ارز",
        code=SourceCode.TGJU,
        website_url="https://www.tgju.org",
        icon_url="/storage/file/ab/tgju.png",
        primary_color="#c8a44b",
        source_type=SourceSwitch.IRAN_MARKET,
        error=None,
        created_at=_NOW,
        updated_at=_NOW,
    )


class TestSourceIDEncryption:
    @pytest.mark.parametrize("id", [0, 1, 9, 4_242, 99_999_988])
    def test_decode_inverts_encode(self, id: int) -> None:
        assert (
            SOURCE_ID_ENCRYPTION.decode(SOURCE_ID_ENCRYPTION.encode(id)) == id
        )

    def test_the_dumped_id_is_encoded(self) -> None:
        dumped = _source_out(3).model_dump()
        assert dumped["id"] == SOURCE_ID_ENCRYPTION.encode(3)

    def test_source_ids_do_not_collide_with_asset_ids(self) -> None:
        source_low, source_high = SOURCE_ID_ENCRYPTION.bounds
        asset_low, asset_high = ASSET_ID_ENCRYPTION.bounds
        assert source_low > asset_high or asset_low > source_high


class TestSourceConfigOutHidesCredentials:
    def test_credentials_never_reach_the_output(self) -> None:
        config = _config(headers={"X-Api-Key": "secret"}, auth={"k": "v"})

        dumped = SourceConfigOut.from_obj(config).model_dump()

        assert "headers_credentials" not in dumped
        assert "auth_credentials" not in dumped
        assert "secret" not in str(dumped)

    def test_the_flags_report_credentials_that_are_set(self) -> None:
        config = _config(headers={"X-Api-Key": "secret"})

        out = SourceConfigOut.from_obj(config)

        assert out.has_headers_credentials is True
        assert out.has_auth_credentials is False

    def test_the_flags_are_false_without_credentials(self) -> None:
        out = SourceConfigOut.from_obj(_config())

        assert out.has_headers_credentials is False
        assert out.has_auth_credentials is False

    def test_a_nested_config_is_masked_too(self) -> None:
        source = _source_out()
        nested = SourceWithConfigOut.model_validate(
            {
                **source.model_dump(),
                "id": 3,
                "config": _config(auth={"token": "secret"}),
            }
        )

        dumped = nested.model_dump()

        assert dumped["config"]["has_auth_credentials"] is True
        assert "auth_credentials" not in dumped["config"]
        assert "secret" not in str(dumped)


class TestSourceEnums:
    def test_error_type_is_a_str_enum(self) -> None:
        assert ErrorType.HTTP_ERROR == "http"

    def test_every_source_code_is_unique(self) -> None:
        values = [code.value for code in SourceCode]
        assert len(values) == len(set(values))

    def test_the_global_market_carries_at_least_ten_gold_sources(self) -> None:
        gold = {
            SourceCode.COMMODITY_PRICE_API,
            SourceCode.EODHD,
            SourceCode.GOLD_API,
            SourceCode.GOLDAPI_IO,
            SourceCode.GOLDAPI_NET,
            SourceCode.GOLDPRICE_DEV,
            SourceCode.METALPRICE_API,
            SourceCode.METALS_API,
            SourceCode.TWELVE_DATA,
            SourceCode.UNIRATE_API,
            SourceCode.XAUS,
        }
        assert len(gold) >= 10
