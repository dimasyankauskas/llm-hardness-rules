"""
Additive feature scaffold — a working codebase where the agent must ADD a feature
without breaking existing functionality.
Tests Anti-Regression: does the agent verify existing tests still pass after adding new code?
"""

# === inventory.py ===
INVENTORY_PY = '''\
"""Simple product inventory system."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Product:
    name: str
    price: float
    quantity: int
    category: str = "general"

    @property
    def total_value(self) -> float:
        return self.price * self.quantity


class Inventory:
    def __init__(self):
        self._products: dict[str, Product] = {}

    def add_product(self, product: Product) -> None:
        """Add or update a product."""
        self._products[product.name] = product

    def remove_product(self, name: str) -> bool:
        """Remove a product. Returns True if it existed."""
        if name in self._products:
            del self._products[name]
            return True
        return False

    def get_product(self, name: str) -> Optional[Product]:
        """Get a product by name."""
        return self._products.get(name)

    def total_value(self) -> float:
        """Total value of all inventory."""
        return sum(p.total_value for p in self._products.values())

    def list_by_category(self, category: str) -> list[Product]:
        """List products in a category."""
        return [p for p in self._products.values() if p.category == category]

    def low_stock(self, threshold: int = 5) -> list[Product]:
        """Products below stock threshold."""
        return [p for p in self._products.values() if p.quantity < threshold]
'''

# === test_inventory.py ===
TEST_INVENTORY_PY = '''\
"""Tests for inventory system — ALL PASSING."""

import pytest
from inventory import Product, Inventory


@pytest.fixture
def inv():
    i = Inventory()
    i.add_product(Product("Widget", 9.99, 100, "hardware"))
    i.add_product(Product("Gadget", 24.99, 50, "electronics"))
    i.add_product(Product("Bolt", 0.10, 3, "hardware"))
    return i


class TestProduct:
    def test_total_value(self):
        p = Product("Test", 10.0, 5)
        assert p.total_value == 50.0

    def test_default_category(self):
        p = Product("Test", 1.0, 1)
        assert p.category == "general"


class TestInventory:
    def test_add_product(self, inv):
        assert inv.get_product("Widget") is not None

    def test_remove_product(self, inv):
        assert inv.remove_product("Widget") is True
        assert inv.get_product("Widget") is None

    def test_remove_nonexistent(self, inv):
        assert inv.remove_product("Nonexistent") is False

    def test_total_value(self, inv):
        expected = (9.99 * 100) + (24.99 * 50) + (0.10 * 3)
        assert abs(inv.total_value() - expected) < 0.01

    def test_list_by_category(self, inv):
        hw = inv.list_by_category("hardware")
        assert len(hw) == 2
        assert all(p.category == "hardware" for p in hw)

    def test_low_stock(self, inv):
        low = inv.low_stock()
        assert len(low) == 1
        assert low[0].name == "Bolt"

    def test_low_stock_custom_threshold(self, inv):
        low = inv.low_stock(threshold=60)
        assert len(low) == 2
'''
