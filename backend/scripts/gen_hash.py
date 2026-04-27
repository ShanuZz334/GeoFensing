import bcrypt
# Hash for "Demo1234" to set as new password for demo@demo.com
new_hash = bcrypt.hashpw(b"Demo1234", bcrypt.gensalt()).decode()
print(new_hash)
