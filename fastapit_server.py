"""Python FastAPI WebApp Auth0 integration example
"""

import json

from os import environ as env
from urllib.parse import quote_plus, urlencode

import uvicorn

from authlib.integrations.starlette_client import OAuth
from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config


# from flask import Flask, redirect, render_template, session, url_for

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = FastAPI()

templates = Jinja2Templates(directory="templates")

# app.secret_key = env.get("APP_SECRET_KEY")
app.add_middleware(SessionMiddleware, secret_key=env.get("APP_SECRET_KEY"))


oauth = OAuth()


oauth.register(
    name="auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


# Controllers API
# `@app.route("/")
# def home():
#     return render_template(
#         "home.html",
#         session=session.get("user"),
#         pretty=json.dumps(session.get("user"), indent=4),
#     )
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "session": user, "pretty": json.dumps(user, indent=4)},
    )


# @app.route("/callback", methods=["GET", "POST"])
# def callback():
#     token = oauth.auth0.authorize_access_token()
#     session["user"] = token
#     return redirect("/")


@app.get("/callback")
async def callback(request: Request):
    auth0_client = oauth.create_client("auth0")
    token = await auth0_client.authorize_access_token(request)
    request.session["user"] = token
    return RedirectResponse(url="/")


# @app.route("/login")
# def login():
#     return oauth.auth0.authorize_redirect(
#         redirect_uri=url_for("callback", _external=True)
#     )
@app.get("/login")
async def login(request: Request):
    auth0_client = oauth.create_client("auth0")
    redirect_uri = request.url_for("callback")
    return await auth0_client.authorize_redirect(request, redirect_uri)


# @app.route("/logout")
# def logout():
#     session.clear()
#     return redirect(
#         "https://"
#         + env.get("AUTH0_DOMAIN")
#         + "/v2/logout?"
#         + urlencode(
#             {
#                 "returnTo": url_for("home", _external=True),
#                 "client_id": env.get("AUTH0_CLIENT_ID"),
#             },
#             quote_via=quote_plus,
#         )
#     )`
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(
        url=f"https://{env.get('AUTH0_DOMAIN')}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.url_for("home"),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(env.get("PORT", 3000)))
