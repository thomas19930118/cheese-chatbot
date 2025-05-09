from utils.flatten_dict import flatten_dict
def flatten_pinecone_metadata(data):
    flat = {
        "image": data.get("image"),
        "url": data.get("url"),
        "name": data.get("name"),
        "brand": data.get("brand"),
        "category": data.get("category"),
        "SKU": data.get("SKU"),
        "UPC": data.get("UPC"),
        "Warning": data.get("Warning")
    }
    # CASE fields (if present)
    case = data.get("CASE", {})
    flat.update({
        "case_count": case.get("count"),
        "case_dimension": case.get("dimension"),
        "case_weight": case.get("weight"),
        "case_price": case.get("price"),
        "case_price_per_lb": case.get("price_per_lb")
    })
    # EACH fields (if present)
    each = data.get("EACH", {})
    flat.update({
        "each_count": each.get("count"),
        "each_dimension": each.get("dimension"),
        "each_weight": each.get("weight"),
        "each_price": each.get("price"),
        "each_price_per_lb": each.get("price_per_lb")
    })
    # Optionally: First related item (if needed)
    rel = data.get("related_items")
    if rel == "None":
        flat.update({
            "related_items":"None"
        })
    else:
        rel_item = []
        for i in rel:
            rel_item.append(flatten_dict(i))
            flat.update({
                "related_items":rel_item
            })
    return {k: v for k, v in flat.items() if v is not None}
