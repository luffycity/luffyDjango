def gen_token(username):
    import time
    import hashlib
    ctime = str(time.time())
    hash = hashlib.md5(username.encode('utf-8'))
    hash.update(ctime.encode('utf-8'))
    return hash.hexdigest()