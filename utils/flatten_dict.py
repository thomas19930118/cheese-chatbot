import json

def flatten_dict(d):
    parts = []
    for k, v in d.items():
        if isinstance(v, dict):
            v = json.dumps(v, separators=(',',':'))  # Keep nested dict compact as JSON
        parts.append(f"{k}:{v}")
    return ', '.join(parts)
