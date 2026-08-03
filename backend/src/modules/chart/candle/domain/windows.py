from typing import Self

from pydantic import BaseModel


class PriceWindow(BaseModel):
    open: int
    high: int
    low: int
    close: int

    def folded(self, price: int) -> Self:
        """
        Desc: Take one more price into the window.
        Args:
            price (int): What the last read said.
        Returns:
            return (Self): The window as it stands with that price in it.
        """
        return self.model_copy(
            update={
                "high": max(self.high, price),
                "low": min(self.low, price),
                "close": price,
            }
        )


class AssetPriceWindow(PriceWindow):
    asset_id: int

    @classmethod
    def opened(cls, asset_id: int, price: int) -> Self:
        """
        Desc: Open an asset's window on the price that opened it.
        Args:
            asset_id (int): ID of the asset being priced.
            price (int): The first price of the window.
        Returns:
            return (Self): The window, flat on that one price.
        """
        return cls(
            asset_id=asset_id,
            open=price,
            high=price,
            low=price,
            close=price,
        )


class SourcePriceWindow(PriceWindow):
    source_id: int
    symbol_id: int

    @classmethod
    def opened(
        cls,
        source_id: int,
        symbol_id: int,
        price: int,
    ) -> Self:
        """
        Desc: Open a source's window on the line it quoted.
        Args:
            source_id (int): ID of the source that quoted it.
            symbol_id (int): ID of the line it was quoted for.
            price (int): The first price of the window.
        Returns:
            return (Self): The window, flat on that one price.
        """
        return cls(
            source_id=source_id,
            symbol_id=symbol_id,
            open=price,
            high=price,
            low=price,
            close=price,
        )
