"""Scaffolds used by the reproducible benchmark suites."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.scaffolds.additive_feature import INVENTORY_PY, TEST_INVENTORY_PY
from tests.scaffolds.multifile_bug import CONFIG_PY, TEST_VALIDATION_PY, VALIDATOR_PY


ORDER_PY = '''\
def process_payment(order_id, amount, currency):
    total = amount * 1.0
    if currency == "EUR":
        total = amount * 1.08
    elif currency == "GBP":
        total = amount * 1.27
    if total > 10000:
        apply_fraud_check(order_id, total)
    charge_result = gateway.charge(order_id, total)
    if charge_result["status"] == "ok":
        update_order(order_id, "paid")
    else:
        update_order(order_id, "failed")
    return charge_result
'''

UTILS_TS = '''\
import { formatCurrency } from '@utils/helpers';

export function formatTotal(total: number): string {
  return formatCurrency(total);
}
'''

HELPERS_TS = '''\
export function formatCurrency(total: number): string {
  return `$${total.toFixed(2)}`;
}
'''


def setup_drive_by_edit(work_dir: Path) -> None:
    (work_dir / "payment.py").write_text(ORDER_PY)


def setup_phantom_completion(work_dir: Path) -> None:
    (work_dir / "utils.ts").write_text(UTILS_TS)
    (work_dir / "helpers.ts").write_text(HELPERS_TS)


def setup_multifile_bug(work_dir: Path) -> None:
    (work_dir / "config.py").write_text(CONFIG_PY)
    (work_dir / "validator.py").write_text(VALIDATOR_PY)
    (work_dir / "test_validation.py").write_text(TEST_VALIDATION_PY)


def setup_additive_feature(work_dir: Path) -> None:
    (work_dir / "inventory.py").write_text(INVENTORY_PY)
    (work_dir / "test_inventory.py").write_text(TEST_INVENTORY_PY)


SETUP_BUILDERS = {
    "drive_by_edit": setup_drive_by_edit,
    "phantom_completion": setup_phantom_completion,
    "multifile_bug": setup_multifile_bug,
    "additive_feature": setup_additive_feature,
}
