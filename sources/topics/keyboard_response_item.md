# keyboard_response item 

- Correct response: Indicates which response should be considered correct. Specify a key name (e.g. 'space') or a Python expression that refers to a variable (e.g. `{my_correct_response}`). Usually this field is left empty, in which case the variable `correct_response` is automatically used when defined.
- Timeout: a numeric duration in milliseconds or 'infinite' for no timeout. When a timeout occurs, the `response` variable is set to `None`.

More information:

- <https://osdoc.cogsci.nl/4.0/manual/response/keyboard/>
