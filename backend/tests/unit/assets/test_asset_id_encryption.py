from datetime import datetime

import pytest

from src.common.bases.encryption import IDEncryption
from src.common.errors.exceptions import NotFoundException
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.assets.domain.schemas import AssetOut
from src.web.dependencies import decode_path_id


def _asset_out(id: int) -> AssetOut:
    """
    Desc: Build an AssetOut carrying the given internal id.
    Args:
        id (int): The internal id.
    Returns:
        return (AssetOut): The output schema.
    """
    now = datetime(2026, 7, 29, 12, 0, 0)
    return AssetOut(
        id=id,
        title="طلای ۱۸ عیار",
        code=AssetCode.GOLD18,
        description=None,
        created_at=now,
        updated_at=now,
    )


class TestIDEncryption:
    @pytest.mark.parametrize("id", [0, 1, 2, 17, 5_000, 99_999_988])
    def test_decode_inverts_encode(self, id: int) -> None:
        assert ASSET_ID_ENCRYPTION.decode(ASSET_ID_ENCRYPTION.encode(id)) == id

    def test_encode_is_injective(self) -> None:
        public = {ASSET_ID_ENCRYPTION.encode(id) for id in range(1, 500)}
        assert len(public) == 499

    def test_public_ids_stay_within_bounds(self) -> None:
        low, high = ASSET_ID_ENCRYPTION.bounds
        for id in (0, 1, 12_345, 99_999_988):
            assert low <= ASSET_ID_ENCRYPTION.encode(id) <= high

    def test_encode_does_not_leak_the_internal_id(self) -> None:
        assert ASSET_ID_ENCRYPTION.encode(1) != 1

    def test_try_decode_rejects_an_out_of_range_id(self) -> None:
        low, _ = ASSET_ID_ENCRYPTION.bounds
        assert ASSET_ID_ENCRYPTION.try_decode(low - 1) is None

    def test_encode_rejects_an_id_past_capacity(self) -> None:
        with pytest.raises(OverflowError):
            ASSET_ID_ENCRYPTION.encode(ASSET_ID_ENCRYPTION.capacity)

    def test_a_non_coprime_coefficient_is_refused(self) -> None:
        with pytest.raises(ValueError):
            IDEncryption(mod=10, coff=4)


class TestAssetOutIDSerialization:
    def test_the_id_stays_internal_in_memory(self) -> None:
        assert _asset_out(7).id == 7

    def test_the_dumped_id_is_encoded(self) -> None:
        dumped = _asset_out(7).model_dump()
        assert dumped["id"] == ASSET_ID_ENCRYPTION.encode(7)

    def test_a_revalidation_never_double_encodes(self) -> None:
        # FastAPI re-validates through response_model; the encode must not
        # compound across that second pass
        once = _asset_out(7).model_dump()
        twice = AssetOut.model_validate(_asset_out(7)).model_dump()
        assert once["id"] == twice["id"]


class TestDecodePathID:
    def test_a_public_id_resolves_to_the_internal_one(self) -> None:
        resolve = decode_path_id(ASSET_ID_ENCRYPTION, "Asset")
        public = ASSET_ID_ENCRYPTION.encode(42)
        assert resolve(id=public) == 42

    def test_a_malformed_id_raises_not_found(self) -> None:
        resolve = decode_path_id(ASSET_ID_ENCRYPTION, "Asset")
        with pytest.raises(NotFoundException):
            resolve(id=1)

    def test_the_dependency_is_named_after_the_path_param(self) -> None:
        resolve = decode_path_id(ASSET_ID_ENCRYPTION, "Asset", "asset_id")
        params = list(resolve.__signature__.parameters)  # type: ignore
        assert params == ["asset_id"]
