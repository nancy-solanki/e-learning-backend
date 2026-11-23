from hashlib import sha256


def user_profile_cache_key(user_id):
    digest = sha256(str(user_id).encode()).hexdigest()
    return f"user-profile:{digest}"
