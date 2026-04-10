"""
utils/inventory_utils.py
─────────────────────────
Inventory management linked to invoices.
When an invoice is accepted, inventory levels are automatically updated.
"""

from datetime import datetime
import uuid

from app.db.supabase_client import db_insert, db_select, db_update

INVENTORY_TABLE = "inventory"
INVENTORY_LOG_TABLE = "inventory_logs"


async def update_inventory_from_invoice(invoice_data: dict, direction: str) -> list[dict]:
    """
    Update inventory based on invoice line items.

    Args:
        invoice_data: Extracted invoice dict with line_items.
        direction: "in" (purchase/inward) | "out" (sale/outward)

    Returns:
        List of updated inventory records.
    """
    line_items = invoice_data.get("line_items") or []
    seller_gstin = invoice_data.get("seller_gstin", "")
    buyer_gstin = invoice_data.get("buyer_gstin", "")

    # The relevant GSTIN is the buyer for inward, seller for outward
    owner_gstin = buyer_gstin if direction == "in" else seller_gstin

    updated_records = []
    for item in line_items:
        hsn = item.get("hsn_sac_code", "")
        description = item.get("description", "")
        quantity = float(item.get("quantity") or 0)
        unit = item.get("unit", "")

        # Look up existing inventory record
        existing = await db_select(INVENTORY_TABLE, {
            "gstin": owner_gstin,
            "hsn_sac_code": hsn,
        })

        if existing:
            record = existing[0]
            current_qty = float(record.get("quantity") or 0)
            new_qty = current_qty + quantity if direction == "in" else current_qty - quantity
            new_qty = max(0.0, new_qty)   # Floor at 0

            updated = await db_update(
                INVENTORY_TABLE,
                {"id": record["id"]},
                {
                    "quantity": new_qty,
                    "last_updated": datetime.utcnow().isoformat(),
                },
            )
            updated_records.append(updated)
        else:
            # Create new inventory entry (only for inward)
            if direction == "in":
                new_record = {
                    "id": str(uuid.uuid4()),
                    "gstin": owner_gstin,
                    "hsn_sac_code": hsn,
                    "description": description,
                    "quantity": quantity,
                    "unit": unit,
                    "last_updated": datetime.utcnow().isoformat(),
                }
                await db_insert(INVENTORY_TABLE, new_record)
                updated_records.append(new_record)

        # Log the movement
        await db_insert(INVENTORY_LOG_TABLE, {
            "id": str(uuid.uuid4()),
            "gstin": owner_gstin,
            "hsn_sac_code": hsn,
            "direction": direction,
            "quantity_change": quantity if direction == "in" else -quantity,
            "invoice_number": invoice_data.get("invoice_number"),
            "created_at": datetime.utcnow().isoformat(),
        })

    return updated_records


async def get_inventory(gstin: str) -> list[dict]:
    """Return current inventory snapshot for a business."""
    return await db_select(INVENTORY_TABLE, {"gstin": gstin})


async def get_low_stock_alerts(gstin: str, threshold: float = 10.0) -> list[dict]:
    """Return inventory items below the threshold quantity."""
    inventory = await get_inventory(gstin)
    return [i for i in inventory if float(i.get("quantity") or 0) <= threshold]