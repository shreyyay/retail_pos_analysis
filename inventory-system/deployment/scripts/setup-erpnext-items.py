"""
Setup sample items in ERPNext for testing the Inventory System.

Usage:
    python setup-erpnext-items.py --url http://localhost:8080 --key <api_key> --secret <api_secret>
"""

import argparse
import requests
import json

SAMPLE_ITEMS = [
    {
        "item_code": "PARLE-G-50G",
        "item_name": "Parle-G 50g",
        "item_group": "Products",
        "stock_uom": "Nos",
        "standard_rate": 10.00,
        "is_stock_item": 1,
        "barcodes": [{"barcode": "8901234567890", "barcode_type": "EAN"}],
        "reorder_level": 50,
    },
    {
        "item_code": "BRITANNIA-100G",
        "item_name": "Britannia Good Day 100g",
        "item_group": "Products",
        "stock_uom": "Nos",
        "standard_rate": 25.00,
        "is_stock_item": 1,
        "barcodes": [{"barcode": "8901234567891", "barcode_type": "EAN"}],
        "reorder_level": 30,
    },
    {
        "item_code": "MAGGI-NOODLES",
        "item_name": "Maggi 2-Minute Noodles",
        "item_group": "Products",
        "stock_uom": "Nos",
        "standard_rate": 14.00,
        "is_stock_item": 1,
        "barcodes": [{"barcode": "8901234567892", "barcode_type": "EAN"}],
        "reorder_level": 100,
    },
    {
        "item_code": "AMUL-BUTTER-100G",
        "item_name": "Amul Butter 100g",
        "item_group": "Products",
        "stock_uom": "Nos",
        "standard_rate": 56.00,
        "is_stock_item": 1,
        "barcodes": [{"barcode": "8901234567893", "barcode_type": "EAN"}],
        "reorder_level": 20,
    },
    {
        "item_code": "TATA-TEA-250G",
        "item_name": "Tata Tea Gold 250g",
        "item_group": "Products",
        "stock_uom": "Nos",
        "standard_rate": 115.00,
        "is_stock_item": 1,
        "barcodes": [{"barcode": "8901234567894", "barcode_type": "EAN"}],
        "reorder_level": 15,
    },
]


def create_item(base_url: str, headers: dict, item: dict) -> bool:
    """Create a single item in ERPNext."""
    item_data = {
        "doctype": "Item",
        "item_code": item["item_code"],
        "item_name": item["item_name"],
        "item_group": item["item_group"],
        "stock_uom": item["stock_uom"],
        "standard_rate": item["standard_rate"],
        "is_stock_item": item["is_stock_item"],
        "barcodes": item.get("barcodes", []),
    }

    # Set reorder level
    if item.get("reorder_level"):
        item_data["reorder_levels"] = [
            {
                "warehouse": "Stores - My Company",
                "warehouse_reorder_level": item["reorder_level"],
                "warehouse_reorder_qty": item["reorder_level"] * 2,
            }
        ]

    try:
        resp = requests.post(
            f"{base_url}/api/resource/Item",
            json=item_data,
            headers=headers,
            timeout=30,
        )
        if resp.status_code == 200:
            print(f"  Created: {item['item_code']} - {item['item_name']}")
            return True
        elif resp.status_code == 409:
            print(f"  Exists:  {item['item_code']} (skipped)")
            return True
        else:
            print(f"  FAILED:  {item['item_code']} - {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"  ERROR:   {item['item_code']} - {e}")
        return False


def ensure_item_group(base_url: str, headers: dict):
    """Ensure 'Products' item group exists."""
    try:
        resp = requests.get(
            f"{base_url}/api/resource/Item Group/Products",
            headers=headers,
            timeout=15,
        )
        if resp.status_code == 200:
            return

        requests.post(
            f"{base_url}/api/resource/Item Group",
            json={
                "doctype": "Item Group",
                "item_group_name": "Products",
                "parent_item_group": "All Item Groups",
            },
            headers=headers,
            timeout=15,
        )
        print("  Created item group: Products")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="Setup sample items in ERPNext")
    parser.add_argument("--url", required=True, help="ERPNext URL (e.g. http://localhost:8080)")
    parser.add_argument("--key", required=True, help="ERPNext API Key")
    parser.add_argument("--secret", required=True, help="ERPNext API Secret")
    args = parser.parse_args()

    headers = {
        "Authorization": f"token {args.key}:{args.secret}",
        "Content-Type": "application/json",
    }

    print(f"\nSetting up sample items in ERPNext at {args.url}\n")

    # Test connection
    try:
        resp = requests.get(f"{args.url}/api/method/frappe.auth.get_logged_user", headers=headers, timeout=10)
        resp.raise_for_status()
        user = resp.json().get("message", "Unknown")
        print(f"Connected as: {user}\n")
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Check your URL and API credentials.")
        return

    ensure_item_group(args.url, headers)

    print("Creating items:")
    success = sum(1 for item in SAMPLE_ITEMS if create_item(args.url, headers, item))
    print(f"\nDone: {success}/{len(SAMPLE_ITEMS)} items created.")


if __name__ == "__main__":
    main()
