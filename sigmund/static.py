import logging
logger = logging.getLogger('sigmund')


db_initialized = False


def predict(prompt, model: str, json: bool = False,
            max_json_retry: int = 5) -> str:
    """Provides a static interface to predict a single response."""
    from .database.models import init_db
    from .model import model as sigmund_model
    global db_initialized
    if not db_initialized:
        init_db()
        db_initialized = True
    model = sigmund_model(None, model)
    if not json:
        return model.predict(prompt)
    import json
    model.json_mode = True
    for _ in range(max_json_retry):
        try:
            return json.loads(model.predict(prompt))
        except Exception as e:
            logger.warning(f'failed to predict JSON: {e}')
            continue
    raise ValueError(f'Failed after {max_json_retry} attempts')
