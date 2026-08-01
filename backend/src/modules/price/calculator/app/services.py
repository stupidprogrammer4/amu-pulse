from typing import Sequence

from src.common.errors.exceptions import NotFoundException
from src.core import resources
from src.modules.price.assets.domain.enums import AssetCode
from src.modules.price.calculator.app.helpers import Aggregator
from src.modules.price.calculator.domain.context import BubbleContext
from src.modules.price.calculator.domain.results import BubbleResult
from src.modules.price.calculator.infra.cache import BubbleCache
from src.modules.price.calculator.infra.readers import BubbleReader
from src.modules.price.engine.domain.results import SourceBubbleResult
from src.modules.price.engine.interfaces import ICacheReaderService


class BubbleCalculatorService:
    def __init__(
        self,
        bubbles: BubbleReader,
        published: ICacheReaderService,
        cache: BubbleCache,
    ) -> None:
        """
        Desc: Build the service with what it settles premiums out of.
        Args:
            bubbles (BubbleReader): Reader over the bubbles module's tables.
            published (ICacheReaderService): Where the crawl left what each
                source published.
            cache (BubbleCache): Where the settled premium lands.
        """
        self.bubbles = bubbles
        self.published = published
        self.cache = cache
        self.aggregator = Aggregator()

    def _settled(
        self,
        bubble: BubbleContext,
        published: Sequence[SourceBubbleResult],
    ) -> BubbleResult | None:
        """
        Desc: Fold every published premium of one asset into a settled one.
        Args:
            bubble (BubbleContext): The bubble being settled, with the rule
                its publishers are folded by.
            published (Sequence[SourceBubbleResult]): What each source
                published for that asset.
        Returns:
            return (BubbleResult | None): The settled premium, or None when
                nobody published one.
        """
        result = None
        if published:
            amount = self.aggregator.pick(
                [row.amount for row in published],
                bubble.config.agg_type,
            )
            result = BubbleResult(
                asset_id=published[0].asset_id,
                amount=amount,
                priced_at=max(row.priced_at for row in published),
            )
        return result

    async def calculate(self, bubble_id: int) -> int:
        """
        Desc: Settle one bubble out of what its publishers last said.
        Args:
            bubble_id (int): ID of the bubble to settle.
        Returns:
            return (int): The settled premium in rial, signed, and zero
                when nobody published one.
        """
        bubble = await self.bubbles.get_bubble_config(bubble_id)
        if bubble is None:
            raise NotFoundException(
                identifier="id",
                identifier_value=bubble_id,
                message=f"Cannot find Bubble by id with value {bubble_id}",
                message_code=resources.NOT_FOUND_ERROR,
                entity="Bubble",
            )
        published = await self.published.get_bubbles_by_asset(bubble.code)
        result = self._settled(bubble, published)
        amount = 0
        if result is not None:
            await self.cache.set(bubble.code, result)
            amount = result.amount
        return amount

    async def calculate_all(self) -> int:
        """
        Desc: Settle every bubble out of what its publishers last said.
        Returns:
            return (int): How many bubbles were settled.
        """
        bubbles = await self.bubbles.get_all()
        published = await self.published.get_all_bubbles()
        settled: dict[AssetCode, BubbleResult] = {}
        for bubble in bubbles:
            result = self._settled(bubble, published.get(bubble.code, ()))
            if result is not None:
                settled[bubble.code] = result
        if settled:
            await self.cache.set_many(settled)
        return len(settled)
