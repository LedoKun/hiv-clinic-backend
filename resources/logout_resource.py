from flask_restful import Resource
from backend.app import logger
from flask_jwt_extended import jwt_required, get_raw_jwt
from backend.models import RevokedToken


class LogoutResource(Resource):
    @jwt_required
    def post(self):
        jti = get_raw_jwt()["jti"]

        try:
            revoked_token = RevokedToken(jti=jti)
            revoked_token.add()
            return {"message": "Access token has been revoked"}

        except Exception as e:
            logger.debug(e)
            return {"message": "Something went wrong"}, 500
