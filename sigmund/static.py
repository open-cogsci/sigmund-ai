import logging
logger = logging.getLogger('sigmund')


db_initialized = False


def predict(prompt, model: str, json: bool = False,
            max_json_retry: int = 5) -> str | dict:
    """Provides a static interface to predict a single response.

    Parameters
    ----------
    prompt : str
        The prompt to predict a response for.
    model : str
        The model to use for prediction.
    json : bool, optional
        Whether to return the response as JSON, by default False.
    max_json_retry : int, optional
        The maximum number of retries to attempt if the response is not valid
        JSON, by default 5.

    Returns
    -------
    str | dict
        The predicted response. If json=True, the response is a dict, otherwise
        it is a str.
    """
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
    from .model import BaseModel
    model.json_mode = True
    for _ in range(max_json_retry):
        reply = model.predict(prompt)
        reply = BaseModel.extract_thinking_block(reply)[0]
        if reply.startswith('```json'):
            reply = reply[7:]
        if reply.startswith('```'):
            reply = reply[3:]
        if reply.endswith('```'):
            reply = reply[:-3]
        try:
            return json.loads(reply)
        except Exception as e:
            logger.warning(f'failed to predict JSON: {e}')
            continue
    raise ValueError(f'Failed after {max_json_retry} attempts')
