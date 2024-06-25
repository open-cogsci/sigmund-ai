In my trial sequence I have a keyboard response item, followed by a sketchpad item. I only want to present the sketchpad item if the participant responds with 3, 4 or 5 to the keyboard response item. If they answer 1 or 2, they should go to the next trial. How can I do this? 

The answer should:

-	Instruct the user: within your trial sequence, go to the run-if field of the sketchpad and enter the following conditional expression:  `response == 3 or response == 4 or response == 5`. It is also correct if the following conditional expression is provided: `response in [3, 4, 5]`. 

The answer should *not*: 

-	Place quotation marks around the participants responses, for example: `response == ‘3’ or response == '4' or response == '5'” or “response in ['3', '4', '5']`
-   Use only a single equal sign for the run-if statement, for example: `response = 3 or response = 4 or response = 5`