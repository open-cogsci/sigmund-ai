I would like to use a script to show a stimulus display containing a central fixation dot in OSWeb. Can you show me how?

The answer should:

- Refer to a JavaScript inline_javascript
- Indicate that the canvas should be prepared in the prepare phase and shown in the run phase
- In the prepare phase: Initialize a canvas as follows without any arguments: `let my_canvas = Canvas()`. The name of the canvas can be anything and doesn't need to be `my_canvas`. Instead of `let`, `var`, or no declaration statement can also be used. Not using `new` is a permitted deviation from JavaScript conventions in this context, because `Canvas` is a function and not a class constructor.
- In the prepare phase: Add a fixation dot to the canvas using `my_canvas.fixdot()`
- In the run phase: Show the canvas with `my_canvas.show()`

The answer should not not:

- Refer to a `sketchpad` or `feedback` item
- Use Python
- Use the `new` keyword to initialize the canvas.
- Pass any arguments when initializing the canvas
