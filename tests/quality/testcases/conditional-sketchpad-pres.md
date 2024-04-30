In my trial sequence I have a keyboard response item, followed by a sketchpad item. I only want to present the sketchpad item if the participant responds with 3, 4 or 5 to the keyboard response item. If they answer 1 or 2, they should go to the next trial. How can I do this? 

The answer should:

-	Instruct the user to navigate to the sequence item that contains the sketchpad item and the keyboard_response item.
-	instruct to click on the sketchpad item to select and in the run-if field of the sketchpad, enter the conditional expression based on the participant’s response: `response == 3 or response == 4 or response == 5` or `response in [3, 4, 5]`. 

The answer should *not*: 

-	Indicate the “run-if” condition is usually found at the bottom of the trial sequence tab
-	Place quotation marks around the participants responses, for example:  `response == ‘3’ or response == '4' or response == '5'” or “response in  ['3', '4', '5']`
-   Use only a single equal sign for the run-if statement, for example: `response = 3 or response = 4 or response = 5`