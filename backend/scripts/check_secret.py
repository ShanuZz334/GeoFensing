import bcrypt
h = "$2a$10$zkb2UBwl67gAskEa.D9YC.sdNPIExbaU9wISqMHBWG6utRV6RLH1W"
# Spring Security uses $2a prefix, Python bcrypt needs $2b
h_bytes = h.replace("$2a$", "$2b$").encode()
candidates = ["password", "Password", "secret", "compreface", "admin", "123456", "Password1"]
for c in candidates:
    try:
        match = bcrypt.checkpw(c.encode(), h_bytes)
        print(f"{c}: {match}")
    except Exception as e:
        print(f"{c}: ERROR {e}")
