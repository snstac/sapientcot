#!/usr/bin/env python3
# Copyright Sensors & Signals LLC https://www.snstac.com
# SPDX-License-Identifier: Apache-2.0
"""SAPIENT (BSI Flex 335) to TAK Gateway."""

__version__ = "0.1.3"

try:
    from .constants import (  # NOQA
        DEFAULT_SAPIENT_HOST,
        DEFAULT_SAPIENT_PORT,
        DEFAULT_COT_TYPE,
        DEFAULT_COT_STALE,
        DEFAULT_SENSOR_COT_TYPE,
        DEFAULT_COT_TYPE_HOSTILE,
        DEFAULT_LEN_BYTES,
        DEFAULT_LEN_ENDIAN,
        AIR_CLASSES,
        CLASS_COT_TYPES,
    )
    from .functions import (  # NOQA
        sapient_to_cot,
        status_to_cot,
        node_location_from_status,
        create_tasks,
    )
    from .classes import SapientWorker  # NOQA
except ImportError as exc:  # pragma: no cover
    import warnings

    warnings.warn(f"COMPAT: ignoring import error: {exc}")
