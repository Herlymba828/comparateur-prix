from typing import Any, Dict


def normalize_ebay_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """Map eBay Browse item to a common offer schema."""
    price = None
    currency = None
    shipping_cost = None

    # Price
    selling = item.get("price") or {}
    price = selling.get("value")
    currency = selling.get("currency")

    # Shipping cost (may be absent)
    shipping = item.get("shippingOptions") or []
    if shipping:
        # choose first option's cost, if present
        cost = (shipping[0] or {}).get("shippingCost") or {}
        shipping_cost = cost.get("value")

    images = item.get("image") or {}
    image_url = images.get("imageUrl")

    seller = (item.get("seller") or {}).get("username")

    return {
        "title": item.get("title"),
        "image": image_url,
        "price": price,
        "currency": currency,
        "shipping_cost": shipping_cost,
        "seller": seller,
        "url": item.get("itemWebUrl"),
        "availability": item.get("availabilityStatus"),
        "marketplace": "ebay",
    }
