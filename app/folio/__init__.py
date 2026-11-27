"""Folio Page."""
import os

VERSION = "2.40.1"
APP_NAME = "Folio Page"
APP_ID = "org.folio.Page"
SHARE = os.environ.get("FOLIO_SHARE") or (os.path.join(os.environ["FOLIO_ROOT"], "share", "folio-page")
                                         if os.environ.get("FOLIO_ROOT") else "/usr/share/folio-page")
