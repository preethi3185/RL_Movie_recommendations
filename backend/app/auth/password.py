from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

# Argon2 is a modern password hashing algorithm that won the Password Hashing Competition.
# It is designed to be resistant to GPU-based cracking attacks by being 'memory-hard',
# meaning it requires a significant amount of RAM to compute a hash.
# This makes it far more secure than older algorithms like SHA-256 or MD5.
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using Argon2.

    The resulting hash includes a unique salt and the algorithm parameters,
    ensuring that identical passwords result in different hashes.
    """
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifies a plain-text password against a stored Argon2 hash.

    The verify method handles the extraction of the salt and parameters
    from the hash before performing the comparison.
    """
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        # Return False if the password does not match or if the hash is malformed.
        return False
