from itertools import combinations

import pytest

from src.common.bases.encryption import IDEncryption
from src.modules.price.assets.config.constants import ASSET_ID_ENCRYPTION
from src.modules.price.bubbles.config.constants import BUBBLE_ID_ENCRYPTION
from src.modules.price.sources.config.constants import SOURCE_ID_ENCRYPTION

_ENCRYPTIONS = {
    "asset": ASSET_ID_ENCRYPTION,
    "source": SOURCE_ID_ENCRYPTION,
    "bubble": BUBBLE_ID_ENCRYPTION,
}


class TestBubbleIDEncryption:
    @pytest.mark.parametrize("id", [0, 1, 5, 777, 99_999_988])
    def test_decode_inverts_encode(self, id: int) -> None:
        assert (
            BUBBLE_ID_ENCRYPTION.decode(BUBBLE_ID_ENCRYPTION.encode(id)) == id
        )

    def test_it_owns_the_third_range(self) -> None:
        low, high = BUBBLE_ID_ENCRYPTION.bounds
        assert low == 300_000_000
        assert high < 400_000_000


class TestRangesStayDisjoint:
    @pytest.mark.parametrize(
        "pair", list(combinations(sorted(_ENCRYPTIONS), 2))
    )
    def test_no_two_modules_share_a_public_id(
        self, pair: tuple[str, str]
    ) -> None:
        first: IDEncryption = _ENCRYPTIONS[pair[0]]
        second: IDEncryption = _ENCRYPTIONS[pair[1]]

        low, high = first.bounds
        other_low, other_high = second.bounds

        assert high < other_low or other_high < low

    def test_the_same_internal_id_renders_differently_per_module(
        self,
    ) -> None:
        public = {enc.encode(1) for enc in _ENCRYPTIONS.values()}

        assert len(public) == len(_ENCRYPTIONS)
