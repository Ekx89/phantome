import hmac, hashlib, json, time, uuid

OWNER_SECRET = "PHC-6531F761E6-56998A77075C492493203F5C-2083111039"  # garde ça privé

def make_key(label: str, days_valid: int = 3650):
    kid = uuid.uuid4().hex[:10].upper()
    exp = int(time.time()) + days_valid * 86400
    msg = f"{kid}:{label}:{exp}".encode()
    sig = hmac.new(OWNER_SECRET.encode(), msg, hashlib.sha256).hexdigest()[:24].upper()
    # Format lisible
    return f"PHC-{kid}-{sig}-{exp}"

if __name__ == "__main__":
    label = input("Label (ex: ADMIN): ").strip() or "ADMIN"
    print("\nKEY:\n", make_key(label), "\n")
