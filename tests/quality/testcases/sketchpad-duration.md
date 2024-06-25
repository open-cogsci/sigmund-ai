I want to set the duration of my sketchpad so that the sketchpad only disappears when the participant presses 'm'. I want to use the GUI. How can I do this? 

The answer should: 

-	Instruct the user to set the duration of the sketchpad to `0`
-	Instruct the user to add a keyboard-response item right after the sketchpad and in its properties: set the "Allowed responses" field to `m` (without quotes), which will restrict responses to the "m" key only. 
-   In the keyboard_response item: set the timeout value (or leave it) as `infinite` (default), so the sketchpad stays until the 'm' key is pressed.


The answer should *not*: 

-   Instruct the user to set the duration of the sketchpad to `blank` or `keypress`
-   In the keyboard_response item, set the timeout or duration to `0` 
-   Refer to python inline-script or Java inline_javascript 