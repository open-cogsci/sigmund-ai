# feedback item

The feedback item is used to present visual stimuli. The main difference between a feedback and a sketchpad item is that a sketchpad item is prepared in advance, whereas a feedback item is prepared only at the moment that it is shown. This means that the content of a feedback item (unlike a sketchpad item) can depend on what happened just before the feedback was presented.

It has built-in drawing tools that allow you to easily draw the following elements:

- Text (textline)
- Image
- Fixation dot (fixdot)
- Line
- Arrow
- Rectangle (rect)
- Circle
- Ellipse
- Gabor patch (gabor)
- Noies patch (noise)

Each element has a Show-if expression, which is a Python expression that determines whether or not it should be shown.

The duration of a feedback item is a numeric duration in milliseconds, 'keypress' (to show the display until a key is pressed) or 'mouseclick' (to show the display until a mouse button is clicked).

More information:

- <https://osdoc.cogsci.nl/4.0/manual/stimuli/visual/>
