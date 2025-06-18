How can I design an eye-tracking experiment in OpenSesame using PyGaze to measure fixation duration during a feature search task? I want the participant to press the R key when they spot a red triangle in an image.

The answer should:

- Outline the basic elements necessary to create the experiment by either starting from scratch with a default template or use the eye-tracking template   
- Instruct the user to configure the pygaze\_init item  
- Describe how the trial sequence inside the loop should look like.    
  - If the user is not using the eye-tracking template, go to the practice loop item and build trial sequence with following elements: pygaze\_drift\_correct (optional), pygaze\_start\_recording, sketchpad\_fixation (shows a cross or dot, 0 ms), inline\_script\_measure\_fixation (existing script), sketchpad\_stimulus (shows the main stimulus), keyboard\_response, pygaze\_log (logs fixation duration), pygaze\_stop\_recording  
  - Explain how to adjust the following items: fixation, inline\_script, stimulus, response item and logger  
  - Mentions how to configure the loop item 

Answer should not:

- Provide one, straightforward instruction to design the experiment  
- Refer exclusively to inline script as the main design method

