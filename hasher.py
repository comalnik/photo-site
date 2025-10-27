from werkzeug.security import generate_password_hash

plaintext = input("Insert password to hash: ")

print(generate_password_hash(plaintext))
