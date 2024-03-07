Sigmund is a powerful, privacy-focused AI assistant (or chatbot). It is a web app that built on state-of-the-art large language models (LLMs).


[TOC]


## Sigmund is an OpenSesame expert

If OpenSesame-expert mode is enabled (in the menu), Sigmund searches for relevant sections in the documentation of [OpenSesame](https://osdoc.cogsci.nl/), a program for developing psychology and cognitive-neuroscience experiments. Sigmund also receives a set of fixed instructions designed to enhance its general knowledge of OpenSesame. Sigmund subsequently uses this information to answer questions, and to provide links to relevant pages from the documentation. This technique, which is a variation of so-called Retrieval-Augmented Generation, allows Sigmund to answer questions about OpenSesame much better than other chatbots.

Sigmund is especially good at generating code for (Python) inline_script or inline_javascript items. Try it!

<blockquote>
I want to create a stimulus display in OpenSesame, using a canvas in a Python inline script. It's a bit complex, so please read carefully! There should be:

- A central fixation dot.
- Six shapes in a circular arrangement around the central dot.
- One of these shapes, randomly selected, should be a square. The other shapes should be circles.
- One of these shapes, again randomly selected, should be green. The other shapes should be red.
- Inside each shape there should be a line segment that is tilted 45 degrees clockwise or counterclockwise.
</blockquote>


## Sigmund respects your privacy

Your messages and attachments are encrypted based on a key that is linked to your password. This means that no-one, not even the administrators of Sigmund, are able to access your data. 

Sigmund uses large-language-model APIs provided by third parties. You can choose which model you want to use in the menu. Importantly, none of these third parties uses data that is sent through the API for any purposes other than replying to the request. Specifically, your data will *not* be used to train their models. For more information, see the terms of service of [OpenAI](https://openai.com/enterprise-privacy), [Mistral](https://mistral.ai/terms/), and [Anthropic](https://www.anthropic.com/legal/commercial-terms).


## Things Sigmund can do

The following capabilities are only available when OpenSesame-expert mode is disabled. (This is to avoid overwhelming the model with instructions.)

### Search Google Scholar

Sigmund can search Google Scholar for scientific literature. Try it!

> Do your pupils constrict when you think of something bright, such as a sunny beach? Please base your answer on scientific literature.

Limitation: Sigmund reads abstracts, titles, author lists, etc. but does not spontaneously reads complete articles. To have Sigmund read complete articles, you can either encourage Sigmund to download the article (see below) or upload the article as an attachment yourself.


### Execute Python and R code

Sigmund can not only write Python and R code, but also execute it. Try it!

> Can you write a Python function that returns the number of words in a sentence? Please also write some test cases and execute them to make sure that the function is correct.

Limitation: Sigmund cannot use or generate attachments during code execution and cannot display figures. This will be improved in future versions.


### Download files and web pages

Sigmund can download files and web pages and save them as attachments (see below). Try it!

> Can you download this page for me? https://journalofcognition.org/articles/10.5334/joc.18

Limitation: Sometimes Sigmund gets confused when trying to download something. Some friendly guidance can help.

### Read attachments

Sigmund can read attachments, which can be uploaded by the user (Menu → Attachments) or downloaded by Sigmund itself (see above). Let's assume you've downloaded the file above and try it!

> Can you summarize the attached joc.18 file?

Limitation: Sometimes Sigmund gets confused when trying to read attachments. Some friendly guidance can help.


## Sigmund is open source

The source code of Sigmund is available on GitHub:

- <https://github.com/open-cogsci/sigmund-ai>


## How can I get an account?

Sigmund is currently in limited beta and by invitation only. If you have received an invitation, you can log in using your account from <https://forum.cogsci.nl/>. 
