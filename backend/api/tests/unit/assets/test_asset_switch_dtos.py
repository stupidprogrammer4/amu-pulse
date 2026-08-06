import pytest
from pydantic import ValidationError

from src.modules.price.assets.config.constants import (
    ASSET_SWITCH_ID_ENCRYPTION,
)
from src.modules.price.assets.domain.dtos import (
    AssetSwitchBatchCreate,
    AssetSwitchBatchDelete,
    AssetSwitchCreate,
    AssetSwitchPriorityUpdate,
    AssetSwitchUpdate,
)
from src.modules.price.sources.domain.enums import SourceSwitch


class TestPriority:
    def test_zero_is_the_best_level(self) -> None:
        item = AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=0)

        assert item.priority == 0

    def test_a_negative_level_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=-1)

    def test_a_level_past_the_cap_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AssetSwitchCreate(switch=SourceSwitch.SUPPLIER, priority=101)


class TestShapes:
    def test_a_patch_may_carry_one_field(self) -> None:
        patch = AssetSwitchUpdate(priority=3)

        assert patch.to_row() == {"priority": 3}

    def test_one_level_carries_many_markets(self) -> None:
        data = AssetSwitchPriorityUpdate(
            priority=0,
            switches=[SourceSwitch.GLOBAL_MARKET, SourceSwitch.SUPPLIER],
        )

        assert len(data.switches) == 2
        assert data.priority == 0

    def test_many_markets_carry_their_own_levels(self) -> None:
        data = AssetSwitchBatchCreate(
            items=[
                AssetSwitchCreate(
                    switch=SourceSwitch.GLOBAL_MARKET, priority=0
                ),
                AssetSwitchCreate(switch=SourceSwitch.IRAN_MARKET, priority=1),
            ]
        )

        assert [item.priority for item in data.items] == [0, 1]

    def test_an_unknown_market_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AssetSwitchPriorityUpdate(priority=0, switches=["bourse"])


class TestBatchDelete:
    def test_a_public_id_is_decoded(self) -> None:
        public = ASSET_SWITCH_ID_ENCRYPTION.encode(7)

        data = AssetSwitchBatchDelete(ids=[public])

        assert data.ids == [7]

    def test_an_id_outside_the_range_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            AssetSwitchBatchDelete(ids=[42])
