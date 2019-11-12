import requests
from flask import request, session, Response, redirect
from jose import jwt

from mo_dots import Data, wrap, unwrap
from mo_files import URL
from mo_future import decorate, first, text
from mo_json import value2json, json2value
from mo_kwargs import override
from mo_math import base642bytes, sha256, bytes2base64URL, rsa_crypto
from mo_math.randoms import Random
from mo_threads.threads import register_thread
from mo_times import Date
from mo_times.dates import parse
from pyLibrary.env import http
from pyLibrary.env.flask_wrappers import cors_wrapper, add_flask_rule
from pyLibrary.sql import SQL_DELETE, SQL_WHERE, SQL_FROM
from pyLibrary.sql.sqlite import (
    Sqlite,
    sql_create,
    quote_column,
    sql_eq,
    sql_query,
    sql_insert,
)
from vendor.mo_logs import Log

DEBUG = False
LEEWAY = parse("minute").seconds


def get_token_auth_header():
    """Obtains the access token from the Authorization Header
    """
    try:
        auth = request.headers.get("Authorization", None)
        bearer, token = auth.split()
        if bearer.lower() == "bearer":
            return token
    except Exception as e:
        pass
    Log.error('Expecting "Authorization = Bearer <token>" in header')


def requires_scope(required_scope):
    """
    Determines if the required scope is present in the access token
    """
    return required_scope in session.scope.split()


class Authenticator(object):
    @override
    def __init__(self, flask_app, auth0, permissions, session_manager, device=None):
        if not auth0.domain:
            Log.error("expecting auth0 configuration")

        self.auth0 = auth0
        self.permissions = permissions
        self.session_manager = session_manager

        # ATTACH ENDPOINTS TO FLASK APP
        endpoints = auth0.endpoints
        if not endpoints.login or not endpoints.logout or not endpoints.keep_alive:
            Log.error("Expecting paths for login, logout and keep_alive")

        add_flask_rule(flask_app, endpoints.login, self.login)
        add_flask_rule(flask_app, endpoints.logout, self.logout)
        add_flask_rule(flask_app, endpoints.keep_alive, self.keep_alive)

        if device:
            self.device = device
            db = self.device.db = Sqlite(device.db)
            if not db.about("device"):
                with db.transaction() as t:
                    t.execute(
                        sql_create(
                            "device",
                            {"state": "TEXT PRIMARY KEY", "session_id": "TEXT"},
                        )
                    )
            if device.auth0.redirect_uri != text(
                URL(device.home, path=device.endpoints.callback)
            ):
                Log.error("expecting home+endpoints.callback == auth0.redirect_uri")

            add_flask_rule(flask_app, device.endpoints.register, self.device_register)
            add_flask_rule(flask_app, device.endpoints.status, self.device_status)
            add_flask_rule(flask_app, device.endpoints.login, self.device_login)
            add_flask_rule(flask_app, device.endpoints.callback, self.device_callback)

    def markup_user(self):
        # WHAT IS THE EMPLOY STATUS OF THE USER?
        pass

    def verify_opaque_token(self, token):
        # Opaque Access Token
        url = "https://" + self.auth0.domain + "/userinfo"
        response = http.get_json(url, headers={"Authorization": "Bearer " + token})
        DEBUG and Log.note("content: {{body|json}}", body=response)
        return response

    def verify_jwt_token(self, token):
        jwks = http.get_json("https://" + self.auth0.domain + "/.well-known/jwks.json")
        unverified_header = jwt.get_unverified_header(token)
        algorithm = unverified_header["alg"]
        if algorithm != "RS256":
            Log.error("Expecting a RS256 signed JWT Access Token")

        key_id = unverified_header["kid"]
        key = unwrap(first(key for key in jwks["keys"] if key["kid"] == key_id))
        if not key:
            Log.error("could not find {{key}}", key=key_id)

        try:
            return jwt.decode(
                token,
                key,
                algorithms=algorithm,
                audience=self.auth0.api.identifier,
                issuer="https://" + self.auth0.domain + "/",
            )
        except jwt.ExpiredSignatureError as e:
            Log.error("Token has expired", code=403, cause=e)
        except jwt.JWTClaimsError as e:
            Log.error(
                "Incorrect claims, please check the audience and issuer",
                code=403,
                cause=e,
            )
        except Exception as e:
            Log.error("Problem parsing", cause=e)

    @register_thread
    @cors_wrapper
    def device_register(self, path=None):
        """
        EXPECTING A SIGNED REGISTRATION REQUEST
        RETURN JSON WITH url FOR LOGIN
        """
        now = Date.now().unix
        request_body = request.get_data().strip()
        signed = json2value(request_body.decode("utf8"))
        command = json2value(base642bytes(signed.data).decode("utf8"))
        session.public_key = command.public_key
        rsa_crypto.verify(signed, session.public_key)

        self.session_manager.setup_session(session)
        session.expires = now + parse("10minute").seconds
        session.state = bytes2base64URL(Random.bytes(32))

        with self.device.db.transaction() as t:
            t.execute(
                sql_insert(
                    self.device.table,
                    {"state": session.state, "session_id": session.session_id},
                )
            )
        response = value2json(
            Data(
                session_id=session.session_id,
                interval="5second",
                expiry=session.expires,
                url=URL(
                    self.device.home,
                    path=self.device.endpoints.login,
                    query={"state": session.state},
                ),
            )
        )

        return Response(
            response, headers={"Content-Type": "application/json"}, status=200
        )

    @register_thread
    @cors_wrapper
    def device_status(self, path=None):
        """
        AUTOMATION CAN CALL THIS ENDPOINT TO FIND OUT THE LOGIN STATUS
        RESPOND WITH {"ok":true} WHEN USER HAS LOGGED IN, AND user IS
        ASSOCIATED WITH SESSION
        """
        now = Date.now().unix
        if not session.session_id:
            return Response(
                '{"try_again":false, "status":"no session id"}', status=401
            )
        request_body = request.get_data().strip()
        signed = json2value(request_body.decode("utf8"))
        command = rsa_crypto.verify(signed, session.public_key)

        time_sent = parse(command.timestamp)
        if not (now - LEEWAY <= time_sent < now + LEEWAY):
            return Response(
                '{"try_again":false, "status":"timestamp is not recent"}', status=401
            )
        if session.expires < now:
            return Response(
                '{"try_again":false, "status":"session is too old"}', status=401
            )
        if session.user:
            session.public_key = None
            return Response('{"try_again":false, "status":"verified"}', status=200)

        state_info = self.device.db.query(
            sql_query(
                {
                    "select": "session_id",
                    "from": self.device.table,
                    "where": {"eq": {"state": session.state}},
                }
            )
        )
        if not state_info.data:
            return Response(
                '{"try_again":false, "status":"State has been lost"}', status=401
            )

        return Response('{"try_again":true, "status":"still waiting"}', status=200)

    @register_thread
    @cors_wrapper
    def device_login(self, path=None):
        """
        REDIRECT BROWSER TO AUTH0 LOGIN
        """
        state = request.args.get("state")
        self.session_manager.setup_session(session)
        session.code_verifier = bytes2base64URL(Random.bytes(32))
        code_challenge = bytes2base64URL(sha256(session.code_verifier.encode("utf8")))

        query = Data(
            client_id=self.device.auth0.client_id,
            redirect_uri=self.device.auth0.redirect_uri,
            state=state,
            nonce=bytes2base64URL(Random.bytes(32)),
            code_challenge=code_challenge,
            response_type="code",
            code_challenge_method="S256",
            response_mode="query",
            audience=self.device.auth0.audience,
            scope=self.device.auth0.scope,
        )
        url = str(
            URL("https://" + self.device.auth0.domain + "/authorize", query=query)
        )

        Log.note("Forward browser to {{url}}", url=url)
        return redirect(url, code=302)

    @register_thread
    @cors_wrapper
    def device_callback(self, path=None):
        # HANDLE BROWESR RETURN FROM AUTH0 LOGIN
        error = request.args.get("error")
        if error:
            Log.error("You did it wrong")

        code = request.args.get("code")
        state = request.args.get("state")
        referer = request.headers.get("Referer")
        result = self.device.db.query(
            sql_query(
                {
                    "from": "device",
                    "select": "session_id",
                    "where": {"eq": {"state": state}},
                }
            )
        )
        if not result.data:
            Log.error("expecting valid state")
        device_session_id = result.data[0][0]

        # GO BACK TO AUTH0 TO GET TOKENS
        token_request = {
            "client_id": self.device.auth0.client_id,
            "redirect_uri": self.device.auth0.redirect_uri,
            "code_verifier": session.code_verifier,
            "code": code,
            "grant_type": "authorization_code",
        }
        DEBUG and Log.note(
            "Send token request to Auth0:\n {{request}}", request=token_request
        )
        auth_response = requests.request(
            "POST",
            str(URL("https://" + self.device.auth0.domain, path="oauth/token")),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                # "Referer": str(URL(self.device.auth0.redirect_uri, query={"code": code, "state": state})),
            },
            data=value2json(token_request),
        )

        try:
            auth_result = wrap(auth_response.json())
        except Exception as e:
            Log.error("not json {{value}}", value=auth_response.content, cause=e)

        # VERIFY TOKENS, ADD USER TO DEVICE'S SESSION
        user_details = self.verify_opaque_token(auth_result.access_token)
        self.session_manager.update_session(
            device_session_id,
            {"user": self.permissions.get_or_create_user(user_details)},
        )

        # REMOVE DEVICE SETUP STATE
        with self.device.db.transaction() as t:
            t.execute(
                SQL_DELETE
                + SQL_FROM
                + quote_column(self.device.table)
                + SQL_WHERE
                + sql_eq(state=state)
            )
        Log.note("login complete")
        return Response("Login complete. You may close this page", status=200)

    @register_thread
    @cors_wrapper
    def login(self, path=None):
        """
        EXPECT AN ACCESS TOKEN, RETURN A SESSION TOKEN
        """
        now = Date.now().unix
        try:
            access_token = get_token_auth_header()
            # if access_token.error:
            #     Log.error("{{error}}: {{error_description}}", access_token)
            if len(access_token.split(".")) == 3:
                access_details = self.verify_jwt_token(access_token)
                session.scope = access_details["scope"]

            # ADD TO SESSION
            self.session_manager.setup_session(session)
            user_details = self.verify_opaque_token(access_token)
            session.user = self.permissions.get_or_create_user(user_details)
            session.last_used = now

            self.markup_user()

            return Response(
                value2json(self.session_manager.make_cookie(session)), status=200
            )
        except Exception as e:
            session.user = None
            session.last_used = None
            Log.error("failure to authorize", cause=e)

    @register_thread
    @cors_wrapper
    def keep_alive(self, path=None):
        if not session.session_id:
            Log.error("Expecting a sesison token")
        now = Date.now().unix
        session.last_used = now
        return Response(status=200)

    @register_thread
    @cors_wrapper
    def logout(self, path=None):
        if not session.session_id:
            Log.error("Expecting a sesison token")
        session.user = None
        session.last_used = None
        return Response(status=200)


def verify_user(func):
    """
    VERIFY A user EXISTS IN THE SESSION, PASS IT TO func
    """

    @decorate(func)
    def output(*args, **kwargs):
        # IS THIS A NEW SESSION
        now = Date.now().unix
        user = session.get("user")
        if not user:
            Log.error("must authorize first")

        session.last_used = now
        return func(*args, user=user, **kwargs)

    return output
