from flask_restful import Resource
from backend.models import User
from flask import abort, request
from backend.app import db, logger
from sqlalchemy import exc
from webargs import fields
from webargs.flaskparser import parser
import bcrypt
import time
from flask_jwt_extended import create_access_token
from datetime import timedelta


class LoginResource(Resource):
    def post(self):
        """
        Login User
        """

        logger.debug("Recieved Login POST request.")

        # get post data
        user_args = self.post_data()

        try:
            hashed = (
                db.session.query(User.password)
                .filter_by(username=user_args["username"])
                .first()
            )

            if not hashed:
                # User is not found
                logger.debug(
                    "User {} is not found.".format(user_args["username"])
                )

                # delay to prevent bruteforce
                time.sleep(1)
                abort(403)

            hashed = hashed[0]

        except (IndexError, KeyError, exc.SQLAlchemyError) as e:
            logger.debug(e)
            abort(500)

        if bcrypt.checkpw(user_args["password"].encode(), hashed.encode()):
            logger.debug(
                "User {} logged in successfully.".format(user_args["username"])
            )

            expires = timedelta(days=1)
            access_token = create_access_token(
                identity=user_args["username"], expires_delta=expires
            )

            return {
                "message": "Logged in as {}".format(user_args["username"]),
                "access_token": access_token,
            }

        else:
            logger.debug(
                "User {} logged in failed.".format(user_args["username"])
            )

            # delay to prevent bruteforce
            time.sleep(1)
            abort(403)

    def post_data(self):
        args = {
            "username": fields.String(required=True),
            "password": fields.String(required=True),
        }

        # Phrase args data
        data = parser.parse(args, request)

        return data
