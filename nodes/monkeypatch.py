from threading import Lock

import execution

CPACK_LAST_ID = None
CPACK_OUTPUT_CACHE = {}

_lock = Lock()


def store_bentoml_value(func):
    def wrapped(
        inputs, class_def, unique_id, outputs=None, dynprompt=None, extra_data={}
    ):
        global CPACK_LAST_ID
        if getattr(class_def, "CPACK_NODE", False):
            with _lock:
                CPACK_LAST_ID = unique_id
        if outputs is None:
            outputs = CPACK_OUTPUT_CACHE
        return func(inputs, class_def, unique_id, outputs, dynprompt, extra_data)

    return wrapped


execution.get_input_data = store_bentoml_value(execution.get_input_data)


def set_bentoml_output(output):
    with _lock:
        CPACK_OUTPUT_CACHE[CPACK_LAST_ID] = output
