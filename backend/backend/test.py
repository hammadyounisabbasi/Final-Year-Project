from app.core.security import (
    create_access_token,
    decode_access_token
)


def main():

    payload = {
        "sub": "1",
        "role": "admin"
    }

    token = create_access_token(payload)

    print("====================================")
    print("JWT CREATED")
    print("====================================")
    print(token)

    decoded = decode_access_token(token)

    print("====================================")
    print("JWT DECODED")
    print("====================================")
    print(decoded)


if __name__ == "__main__":
    main()