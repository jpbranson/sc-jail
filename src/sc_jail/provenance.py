"""Storage schemas and research algorithms have independent versions."""

import os

APPLICATION_VERSION = "0.2.0"
PARSER_VERSIONS = {"iml": 1, "xfer": 2, "iml_details": 1, "xfer_courts": 1}
REPEAT_CALCULATION_VERSION = 1


def provenance(source):
    return {"application_version": APPLICATION_VERSION,
            "parser_version": PARSER_VERSIONS[source],
            "build_revision": os.getenv("SCJ_BUILD_REVISION", "development")}
