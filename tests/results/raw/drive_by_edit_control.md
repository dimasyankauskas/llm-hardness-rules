MCP issues detected. Run /mcp list for status.```python
import logging

logger = logging.getLogger(__name__)

def process_payment(order_id, amount, currency):
    logger.info(f"Payment started for order {order_id}: {amount} {currency}")
    total = amount * 1.0
    if currency == 'EUR':
        total = amount * 1.08
    elif currency == 'GBP':
        total = amount * 1.27
    if total > 10000:
        apply_fraud_check(order_id, total)
    charge_result = gateway.charge(order_id, total)
    if charge_result['status'] == 'ok':
        update_order(order_id, 'paid')
    else:
        update_order(order_id, 'failed')
    logger.info(f"Payment completed for order {order_id}: {charge_result['status']}")
    return charge_result
```