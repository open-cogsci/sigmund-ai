I am working on a desktop experiment. How can I create a variable that keeps track of the total amount of correct answers (collected by keyboard_response item), given by the participant? 

The answer should: 

- instruct to initialize a custom variable to keep track of the number of correct answers by placing an inline_script item at the start of the experiment and adding the following code to the prepare tab: `total_correct = 0`. the name of the variable can be anything and does not need to be `total_correct`. 
- after your keyboard_response item, insert another inline_script and add the following code to the run tab: 
`if correct == 1:
    total_correct += 1`

The answer should *not*: 

-	instruct using the prefix "var." when initializing or updating a variable. Examples to avoid include: `initialize var.total_correct = 0` or 
`if var.correct == 1:
    var.total_correct += 1` 