from threading import Lock

import execution

BENTOML_LAST_ID = None
BENTOML_OUTPUT_CACHE = {}

_lock = Lock()


def store_bentoml_value(func):
    def wrapped(
        inputs, class_def, unique_id, outputs=None, dynprompt=None, extra_data={}
    ):
        global BENTOML_LAST_ID
        if getattr(class_def, "BENTOML_NODE", False):
            with _lock:
                BENTOML_LAST_ID = unique_id
        if outputs is None:
            outputs = BENTOML_OUTPUT_CACHE
        return func(inputs, class_def, unique_id, outputs, dynprompt, extra_data)

    return wrapped


execution.get_input_data = store_bentoml_value(execution.get_input_data)


def set_bentoml_output(output):
    with _lock:
        BENTOML_OUTPUT_CACHE[BENTOML_LAST_ID] = output
