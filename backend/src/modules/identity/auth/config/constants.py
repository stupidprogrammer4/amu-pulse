from src.common.bases.encryption import IDEncryption

# prime modulus under the 100M offset step, so each module owns a range
USER_ID_ENCRYPTION = IDEncryption(
    mod=99_999_989,
    coff=48_611_303,
    offset=100_000_000,
)