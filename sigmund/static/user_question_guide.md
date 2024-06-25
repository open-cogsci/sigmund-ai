# How to ask effective questions

This guide provides essential tips to help you ask Sigmund effective questions about OpenSesame. Learn how to clearly define your query, choose the right level of detail, and communicate effectively to get the most accurate and useful responses from Sigmund.

[TOC]

## 1. Optimizing Question Clarity and Detail

To optimize question clarity and detail, follow these tips when asking questions about OpenSesame:

- Be specific and concrete. Include key terms like “sketchpad”, “inline_script”, “OSWeb”, “Python”, “Canvas”, etc. This helps Sigmund find relevant parts of the documentation.
- In OpenSesame, many tasks can be executed using multiple methods. For example, you can display an image either by using the clickable element in a `sketchpad` item, modifying the script of a `sketchpad` item or by adding an `inline_script`. Other examples of tasks for which multiple methods are viable include displaying text, playing sounds, generating and playing sounds, and collecting keyboard or mouse responses. When you want to execute a task using a specific method, it’s best to specify it when it cannot otherwise be derived from your question.
- Find a balance between brevity and detail in your questions. Concise questions are efficient but may miss necessary details, while overly elaborate questions can bury the main issue under too much information.
- Check that your question can likely be answered based on OpenSesame's features and functionality. Sigmund specializes in OpenSesame, but its knowledge of other tools is limited.

### Examples of Effective Questions:

- “How do I present an image using a sketchpad item in OpenSesame?”
- “I want to display a green square in the middle of the screen using Python inline_script. How can I do this?”
- “What's the best way to collect response time data for a task in OSWeb?”
- “How can I randomize the order of blocks in an experiment?”
- “Hi Sigmund, my feedback item doesn’t display the accuracy correctly. Here’s the script: 
  `draw textline color=white text="Accuracy: {accuracy} %" x=0 y=0`
  Any clues what’s wrong?”

### Examples of Less Effective Questions:

- **Unspecific:** “How can I present a distractor stimulus?”
- **No preferred method indicated:** “I want to display a green square in the middle of the screen. How can I do this?" 
- **Lacking necessary detail:** “The feedback item does not display the accuracy correctly. Can you help?”
- **Too elaborate:** “I am running an OpenSesame experiment that provides real-time feedback on participant accuracy, which is crucial for my study on learning and adaptation. I've configured the feedback item to display the accuracy in percentage, but it doesn’t show the correct values. Here is the relevant script:
  `draw textline color=white text="Accuracy: {accuracy} %" x=0 y=0`
  Responses are logged using the `correct_response` variable. I also have a Python inline script to log additional details like reaction times and trial numbers in a separate file. I’ve reviewed the documentation but couldn’t find a solution. I’m using OpenSesame 4.0 with the PsychoPy backend. Could you help me figure out what’s wrong?”


## 2. Scripts and Error Messages

### Scripts

A script is a piece of code that defines and controls various aspects of the experiment, such as stimuli presentation, logic, and data handling. In OpenSesame, scripts are mainly used within the script view of GUI items like a `sketchpad` item, within an `inline_script` item, or within an `inline_javascript` item. Providing Sigmund with your relevant scripts will help Sigmund to best assist you with building your OpenSesame project. Here are some examples of when sharing your script with Sigmund would be helpful:
- When your `inline_script` or GUI item is not working as expected, and you need help identifying why.
- When you want to modify your GUI item script or `inline_script` but are unsure how to do so.

An example of how to provide a `sketchpad`’s script is given below:

<blockquote style="white-space:pre-wrap;">
You: Dear Sigmund, my sketchpad item disappears really quickly and I do not understand why. I provided my sketchpad script below, can you tell me why this is happening?:

set start_response_interval no
set duration 10
set description "Displays stimuli"
draw fixdot color=white show_if=True style=default x=0 y=0 z_index=0
draw textline center=1 color=white font_bold=no font_family=mono font_italic=no font_size=68 html=yes show_if=True text="Example" x=0 y=0 z_index=0

Sigmund: Dear user,
Based on the script you provided, the duration of your sketchpad is set to 10, which means the sketchpad will be displayed for only 10 milliseconds. This very short duration is likely why [...]
</blockquote>

### Error Messages

If you receive error messages and want Sigmund's assistance, it is good practice to copy the error message and include it in your question. This helps Sigmund understand and diagnose the issue.

## 3. Takeaways

In general, when asking a question:

- Include key terms
- Provide the specific issue.
- Include relevant code or settings.
- Indicate which method you prefer to use to execute the task.
- Avoid extraneous details that don't directly relate to the problem.
