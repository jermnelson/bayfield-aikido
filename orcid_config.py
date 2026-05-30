"""Public ORCID OpenID Connect configuration.

Only PUBLIC values live here — there is no client secret in this design.
The implicit flow returns a signed id_token directly in the redirect
fragment, so a static site never needs to authenticate to a token endpoint.

To go live, swap the SANDBOX block for the PRODUCTION block and register a
matching redirect URI in ORCID Developer Tools.
"""

# --- SANDBOX (default) ---
ORCID_BASE = "https://sandbox.orcid.org"
CLIENT_ID = "APP-XXXXXXXXXXXXXXXX"  # public id; fill in after registering a sandbox client
REDIRECT_URI = "http://127.0.0.1:8000/"  # must exactly match a registered redirect URI

# --- PRODUCTION (uncomment to go live) ---
# ORCID_BASE = "https://orcid.org"
# CLIENT_ID = "APP-XXXXXXXXXXXXXXXX"
# REDIRECT_URI = "https://jermnelson.github.io/bayfield-aikido/"

SCOPE = "openid"

# Derived endpoints
AUTHORIZE_URL = ORCID_BASE + "/oauth/authorize"
JWKS_URL = ORCID_BASE + "/oauth/jwks"
ISSUER = ORCID_BASE
