I would like to use a Python script to collect a mouse click press. I would like the mouse cursor to be visible. There should be response timeout of five seconds. Can you show me how?

The answer should:

- Refer to a Python inline_script
- Indicate that the mouse should be prepared in the prepare phase and used to collect a response in the run phase
- In the prepare phase: Initialize a mouse as follows: `my_mouse = Mouse()`. The name of the mouse can be anything and doesn't need to be `my_mouse`.
- In the run phase: Collect a keyboard with `button, pos, t = my_mouse.get_click()`. The name of the variables can be anything and don't need to be `button`, `pos`, and `t`.
- The `timeout` should be specified either during initialization: `my_mouse = Mouse(timeout=2000, visible=True)` or when getting the click: `button, pos, t = my_mouse.get_click(timeout=2000)`
- The visibility should be specified during initialization: `my_mouse = Mouse(visible=True)` or when getting the click: `button, pos, t = my_mouse.get_click(visible=True)` or by calling `my_mouse.show_cursor(show=True)`

The answer should not not:

- Refer to a `mouse_response` item
- Use JavaScript
- Pass `exp` as argument when initializing the mouse, although other arguments may be passed as explained above
