from backend.app import jwt
from backend import models
from flask import jsonify


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token["jti"]

    return models.RevokedToken.is_jti_blacklisted(jti)


# Using the expired_token_loader decorator, we will now call
# this function whenever an expired but otherwise valid access
# token attempts to access an endpoint
@jwt.expired_token_loader
def my_expired_token_callback():
    return (
        jsonify(
            {"status": 401, "sub_status": 42, "msg": "The token has expired"}
        ),
        401,
    )
