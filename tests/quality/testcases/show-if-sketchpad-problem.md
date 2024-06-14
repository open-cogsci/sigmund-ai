In my trial sequence I have a keyboard response item and after that a sketchpad item. For my keyboard response item I have defined allowed responses and the correct response. After the keyboard_response item, I only want to show the sketchpad item if the response, that was collected by the keyboard_response item, was incorrect. However, my if-statement is not working. This is my show_if statement: show_if = correct = 0. Why is it not working and how can I solve this problem?” 

The answer should: 

- Indicate that in an appropriate Python conditional expression `==` should be used for comparison and not `=`. 
- Indicate that "=" functions as an assignment operator in Python, not a comparison. For comparison, one should use "==".
- Explain one cannot use the show-if statement to control the display of a sketchpad based on something that happens earlier during the same trial. 
- Explain the user should use a  run-if statement. For example: in the sketchpad’s properties within the sequence, find the "Run if" field and enter `correct == 0`  
- Instruct the user to set the 'show_if' expression for the sketchpad item to 'show_if=True', enabling it to be ready for conditional execution based on the 'Run if' statement.


The answer should *not*: 

- Imply or state that the 'show_if' condition can be used to control dynamic display properties based on responses or events that happen during the execution of the trial.
- Suggest adjusting the 'show_if' expression to make decisions based on the outcome of events during the trial, such as changing it to `show_if = correct == 0` 
