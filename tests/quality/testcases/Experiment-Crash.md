In my trial sequence I have a multiple-choice test. The sequence includes: a loop item with 4 multiple choice questions, answer options and the correct\_answer variable; then there is a multiple\_choice form and after that there is a sampler with the .ogg file that is supposed to play when the answer is incorrect; the run-if expression of the form is set to response \!= correct\_answer. When I run the experiment, it crashes after the first response is given. The error message I receive is:  Error: ConditionalExpressionError

Error while evaluating run-if expression

This error occurred in the run phase of item question\_sequence.  
Traceback (most recent call last):  
  File "\<conditional statement\>", line 1, in \<module\>

NameError: name 'response' is not defined”

How can I fix the error?

The answer should:

- Clearly explain why the NameError occurred  
- Point the user to the multiple\_choice to check what the “response variable” is and change the run if expression with the correct response variable  
- Emphasise that the expression should be in the Sampler’s run-if expression field

The answer should not:

- Suggest changing the expression to “correct \== 0”

