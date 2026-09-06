# custom_components/autopi

-   `coordinator.py` is the only module that may import `AutoPiClient`. Entities read coordinator
    data; they never call the API themselves.
-   `PLATFORMS` lives in `const.py`, not `__init__.py`. A new platform file is inert until it is
    added there.
-   A new telemetry sensor needs both a class and an entry in `FIELD_ID_TO_SENSOR_CLASS`
    (`data_field_sensors.py`). That dict is the registry entity creation walks _and_ the one
    `scripts/generate_docs.py` reads, so a class with no entry is silently never instantiated and
    silently absent from the generated entity reference.
-   `strings.json` is the source for config-flow text and `translations/en.json` is a hand-maintained
    copy. Add a step or key to one without the other and the UI shows raw keys; the two have drifted
    before.
