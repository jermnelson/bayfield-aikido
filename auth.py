"""ORCID "Sign in with ORCID" via the OpenID Connect implicit flow.

Runs entirely in the browser under PyScript/Pyodide. No backend, no client
secret. The signed id_token (JWT) is returned in the redirect URL fragment,
its signature is verified against ORCID's JWKS, and only the derived
{sub, name, exp} is kept in sessionStorage. The raw token is never persisted
and never written to disk.

State is managed exclusively through browser APIs:
  window.crypto.getRandomValues  -> CSRF `state` + replay `nonce`
  sessionStorage                 -> transient state/nonce + the session
  window.location.hash           -> read the implicit-flow fragment
  history.replaceState           -> strip the token from the URL
"""

import json

import jwt
from js import console, document, history, sessionStorage, window
from pyodide.ffi import create_proxy
from pyodide.http import pyfetch

import orcid_config as cfg

SESSION_KEY = "orcid_session"
STATE_KEY = "orcid_state"
NONCE_KEY = "orcid_nonce"


def _now() -> int:
    """Seconds since epoch, from the browser clock (no Date.now in Pyodide)."""
    return int(window.Date.now() / 1000)


def random_token() -> str:
    """16 cryptographically-random bytes as hex, via the Web Crypto API."""
    buf = window.Uint8Array.new(16)
    window.crypto.getRandomValues(buf)
    return "".join("{:02x}".format(b) for b in buf)


# --- login -----------------------------------------------------------------

def start_login(event=None) -> None:
    """Kick off the implicit flow by redirecting to ORCID's authorize URL."""
    state = random_token()
    nonce = random_token()
    sessionStorage.setItem(STATE_KEY, state)
    sessionStorage.setItem(NONCE_KEY, nonce)

    params = {
        "response_type": "token id_token",
        "client_id": cfg.CLIENT_ID,
        "redirect_uri": cfg.REDIRECT_URI,
        "scope": cfg.SCOPE,
        "nonce": nonce,
        "state": state,
    }
    query = "&".join(
        "{}={}".format(k, window.encodeURIComponent(v)) for k, v in params.items()
    )
    window.location.href = cfg.AUTHORIZE_URL + "?" + query


# --- redirect handling -----------------------------------------------------

def _parse_fragment() -> dict:
    """Parse the `#a=b&c=d` fragment into a dict."""
    frag = window.location.hash
    if frag.startswith("#"):
        frag = frag[1:]
    out = {}
    for pair in frag.split("&"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            out[window.decodeURIComponent(k)] = window.decodeURIComponent(v)
    return out


async def _jwk_for(kid: str):
    """Fetch ORCID's JWKS and return the signing key matching `kid`."""
    resp = await pyfetch(cfg.JWKS_URL)
    jwks = await resp.json()
    for key in jwks["keys"]:
        if key.get("kid") == kid:
            return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
    raise ValueError("no matching JWKS key for kid=" + str(kid))


async def verify_id_token(token: str, nonce: str) -> dict:
    """Verify signature + standard claims and return the decoded payload."""
    header = jwt.get_unverified_header(token)
    key = await _jwk_for(header["kid"])
    claims = jwt.decode(
        token,
        key=key,
        algorithms=["RS256"],
        audience=cfg.CLIENT_ID,
        issuer=cfg.ISSUER,
    )
    if claims.get("nonce") != nonce:
        raise ValueError("nonce mismatch")
    return claims


async def handle_redirect() -> None:
    """If we arrived back from ORCID, validate the token and store the session."""
    frag = _parse_fragment()
    if "id_token" not in frag:
        return

    # Always clear the token-bearing fragment from the URL, success or not.
    history.replaceState(None, "", window.location.pathname)

    expected_state = sessionStorage.getItem(STATE_KEY)
    expected_nonce = sessionStorage.getItem(NONCE_KEY)
    sessionStorage.removeItem(STATE_KEY)
    sessionStorage.removeItem(NONCE_KEY)

    if not expected_state or frag.get("state") != expected_state:
        console.warn("ORCID: state mismatch — ignoring redirect")
        return

    try:
        claims = await verify_id_token(frag["id_token"], expected_nonce)
    except Exception as exc:  # noqa: BLE001 — surface any validation failure
        console.warn("ORCID: id_token rejected — " + str(exc))
        return

    session = {
        "sub": claims["sub"],
        "name": claims.get("name") or claims["sub"],
        "exp": int(claims["exp"]),
    }
    sessionStorage.setItem(SESSION_KEY, json.dumps(session))
    # raw token intentionally dropped here — only {sub, name, exp} survives


# --- session + UI ----------------------------------------------------------

def current_session():
    """Return the active {sub, name, exp} session, or None if absent/expired."""
    raw = sessionStorage.getItem(SESSION_KEY)
    if not raw:
        return None
    try:
        session = json.loads(raw)
    except ValueError:
        sessionStorage.removeItem(SESSION_KEY)
        return None
    if int(session.get("exp", 0)) <= _now():
        sessionStorage.removeItem(SESSION_KEY)
        return None
    return session


def logout(event=None) -> None:
    sessionStorage.removeItem(SESSION_KEY)
    render()


def render() -> None:
    """Toggle between the sign-in button and the signed-in badge."""
    login_btn = document.getElementById("orcid-login")
    badge = document.getElementById("orcid-badge")
    session = current_session()
    if session:
        login_btn.hidden = True
        badge.hidden = False
        badge.innerHTML = (
            "✓ Signed in as <strong>{name}</strong> "
            "&middot; {sub} "
            '<button id="orcid-logout" type="button">Sign out</button>'
        ).format(name=session["name"], sub=session["sub"])
        document.getElementById("orcid-logout").addEventListener(
            "click", create_proxy(logout)
        )
    else:
        badge.hidden = True
        login_btn.hidden = False


async def main() -> None:
    await handle_redirect()
    render()
    document.getElementById("orcid-login").addEventListener(
        "click", create_proxy(start_login)
    )


await main()  # noqa: F704 — PyScript runs this module in an async context
