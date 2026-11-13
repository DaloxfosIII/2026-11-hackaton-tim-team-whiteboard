from .models import StockItem


class InsufficientStock(Exception):
    pass


class UnknownSku(KeyError):
    pass


class InventoryService:
    def __init__(self):
        self._items: dict[str, StockItem] = {}
        self._reservations: dict[str, tuple[str, int]] = {}

    def add_stock(self, sku: str, qty: int) -> None:
        if sku in self._items:
            self._items[sku].on_hand += qty
        else:
            self._items[sku] = StockItem(sku, qty)

    def reserve(self, reservation_id: str, sku: str, qty: int) -> None:
        item = self._items[sku]
        if qty > item.on_hand:
            raise InsufficientStock(sku)
        item.reserved += qty
        self._reservations[reservation_id] = (sku, qty)

    def release(self, reservation_id: str) -> None:
        sku, qty = self._reservations[reservation_id]
        self._items[sku].reserved -= qty

    def fulfil(self, reservation_id: str) -> None:
        sku, qty = self._reservations.pop(reservation_id)
        item = self._items[sku]
        item.on_hand -= qty

    def available(self, sku: str) -> int:
        return self._items[sku].available
