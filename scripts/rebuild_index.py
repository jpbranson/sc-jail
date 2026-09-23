"""Rebuild working checkpoints and the public index from verified observations."""

import json

from sc_jail.archive import rebuild_index
from sc_jail.config import Config
from sc_jail.storage import make_store


def main():
    config = Config.from_env()
    store = make_store(config)
    with store.lease(renewable=True):
        index = rebuild_index(store, history_days=config.history_days)
    print(json.dumps({name: len(state.get("history", []))
                      for name, state in index["sources"].items()}))


if __name__ == "__main__":
    main()
