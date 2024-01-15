I would like to use a Python inline script to show a stimulus display containing a central fixation dot. Can you show me how?

The answer should:

- Refer to a Python inline_script
- Indicate that the canvas should be prepared in the prepare phase and shown in the run phase
- In the prepare phase: Initialize a canvas as follows without any arguments: `my_canvas = Canvas()`. The name of the canvas can be anything and doesn't need to be `my_canvas`.
- In the prepare phase: Add a fixation dot to the canvas using `my_canvas.fixdot()`, `my_canvas += FixDot()`, or `my_canvas['fixdot'] = FixDot()`. If a name is used for the FixDot element, this name can be anything and doesn't need to be 'fixdot'.
- In the run phase: Show the canvas with `my_canvas.show()`

The answer should not not:

- Refer to a `sketchpad` or `feedback` item
- Use JavaScript
- Pass any arguments when initializing the canvas 
