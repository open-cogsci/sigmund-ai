I want the content of my sketchpad to stay on the screen until the participant presses a specific key or until 5 seconds have passed. I want to use the GUI for this. How can I do this? 

The answer should: 

-  make sure that the duration of the  sketchpad is set to `0` 
-  Directly after the sketchpad in the sequence, add a keyboard_response item. 
-  In the keyboard_response item, set the timeout to `5000`. In the 'allowed responses' field, define the specific key(s) that participants can press to end the display and proceed.

The answer should *not*: 

-   In the properties of your sketchpad, set the duration to `5000 ms` , `keypress` , or any value other than `0`
-   Refer to python inline_script
-	Refer to java inline_javascript
