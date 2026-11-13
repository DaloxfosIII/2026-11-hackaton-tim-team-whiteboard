import pytest

from inventory import InsufficientStock, InventoryService, UnknownSku


@pytest.fixture
def svc():
    s = InventoryService()
    s.add_stock("SKU1", 10)
    return s


def test_reserve_and_available(svc):
    svc.reserve("r1", "SKU1", 4)
    assert svc.available("SKU1") == 6


def test_cannot_over_reserve_across_reservations(svc):
    svc.reserve("r1", "SKU1", 7)
    with pytest.raises(InsufficientStock):
        svc.reserve("r2", "SKU1", 5)
    assert svc.available("SKU1") == 3
    svc.reserve("r3", "SKU1", 3)
    assert svc.available("SKU1") == 0


def test_failed_reserve_does_not_register(svc):
    with pytest.raises(InsufficientStock):
        svc.reserve("r1", "SKU1", 11)
    with pytest.raises(KeyError):
        svc.release("r1")


def test_double_release_rejected(svc):
    svc.reserve("r1", "SKU1", 4)
    svc.release("r1")
    assert svc.available("SKU1") == 10
    with pytest.raises(KeyError):
        svc.release("r1")
    assert svc.available("SKU1") == 10


def test_fulfil_consumes_reservation(svc):
    svc.reserve("r1", "SKU1", 4)
    svc.fulfil("r1")
    assert svc.available("SKU1") == 6
    svc.add_stock("SKU1", 4)
    assert svc.available("SKU1") == 10
    with pytest.raises(KeyError):
        svc.fulfil("r1")
    with pytest.raises(KeyError):
        svc.release("r1")


def test_duplicate_reservation_id(svc):
    svc.reserve("r1", "SKU1", 2)
    with pytest.raises(ValueError):
        svc.reserve("r1", "SKU1", 3)
    assert svc.available("SKU1") == 8


@pytest.mark.parametrize("qty", [0, -1])
def test_non_positive_quantities(svc, qty):
    with pytest.raises(ValueError):
        svc.add_stock("SKU1", qty)
    with pytest.raises(ValueError):
        svc.reserve("rx", "SKU1", qty)
    assert svc.available("SKU1") == 10


def test_unknown_sku(svc):
    with pytest.raises(UnknownSku):
        svc.reserve("r1", "NOPE", 1)
    with pytest.raises(UnknownSku):
        svc.available("NOPE")
    assert issubclass(UnknownSku, KeyError)


def test_reservation_ids_are_global_across_skus(svc):
    svc.add_stock("SKU2", 5)
    svc.reserve("r1", "SKU1", 1)
    with pytest.raises(ValueError):
        svc.reserve("r1", "SKU2", 1)
    assert svc.available("SKU2") == 5
