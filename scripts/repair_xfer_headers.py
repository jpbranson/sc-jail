"""Remove repeated spreadsheet headings from existing derived XFER history."""
import json

from sc_jail.config import Config
from sc_jail.repair import repair_xfer_headers
from sc_jail.storage import make_store

if __name__ == "__main__":
    print(json.dumps(repair_xfer_headers(make_store(Config.from_env())), indent=2))
