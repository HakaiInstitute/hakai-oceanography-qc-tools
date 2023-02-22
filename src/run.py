import logging
import os

import plotly.io as pio
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

import index
from utils.hakai_plotly_template import hakai_template
from utils.tools import load_config

# load hakai template
pio.templates["hakai"] = hakai_template
pio.templates.default = "hakai"

config = load_config()
config.update({key: value for key, value in os.environ.items() if key in config})

sentry_logging = LoggingIntegration(
    level=config["SENTRY_LEVEL"],  # Capture info and above as breadcrumbs
    event_level=config["SENTRY_EVENT_LEVEL"],  # Send errors as events
)
sentry_sdk.init(
    dsn=config["SENTRY_DSN"],
    integrations=[
        sentry_logging,
    ],
    traces_sample_rate=1.0,
)

logger = logging.getLogger()
logger.setLevel(config["LOG_LEVEL"])
fileHandler = logging.FileHandler("dashboard.log")
fileHandler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
)
logger.addHandler(fileHandler)


if __name__ == "__main__":
    index.app.run_server(
        host=config["DASH_HOST"],
        port=config["DASH_PORT"],
        debug=config["DASH_DEBUG"] not in (False, "false", "False", 0),
    )
