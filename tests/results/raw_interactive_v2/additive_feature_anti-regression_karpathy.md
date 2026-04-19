MCP issues detected. Run /mcp list for status.I will begin by reading `inventory.py` and `test_inventory.py` to understand the current implementation of the `Inventory` class and its tests.
I will now run the existing tests using `pytest` to confirm they pass before I make any changes.
I will now try running the tests using `python3 -m pytest test_inventory.py` to check for its availability.
I will now add the `apply_discount` method to the `Inventory` class in `inventory.py` and a corresponding test case to `test_inventory.py`.
I will now run the tests again using `python3 -m pytest test_inventory.py` to ensure all tests, including the new one, pass.
I have added the `apply_discount` method to the `Inventory` class in `inventory.py` and a corresponding test in `test_inventory.py`. I then verified that all 10 tests passed successfully.