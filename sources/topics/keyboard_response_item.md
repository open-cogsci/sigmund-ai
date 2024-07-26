# keyboard_response item 

- Correct response: Indicates which response should be considered correct. Specify a key name (e.g. 'space') or a Python expression that refers to a variable (e.g. `{my_correct_response}`). Usually this field is left empty, in which case the variable `correct_response` is automatically used when defined.
- Timeout: a numeric duration in milliseconds or 'infinite' for no timeout. When a timeout occurs, the `response` variable is set to `None`.

A common issue is that a `sketchpad` with a 'keypress' duration is followed by a `keyboard_respones`. In that case, the participant has to press twice in a row (once for the `sketchpad` and once for the `keyboard_response`). The solution is to set the duration of the `sketchpad` to 0, so that the `sketchpad` advances immediately to the `keyboard_response`.

More information:

- <https://osdoc.cogsci.nl/4.0/manual/response/keyboard/>
