from hashlib import blake2b


def make_snapshot_file_name(body) -> str:
    black_object = blake2b(digest_size=16)
    black_object.update(str(body).encode(encoding='utf-8'))
    return f'{black_object.hexdigest()}.json'
