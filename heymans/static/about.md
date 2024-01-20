[TOC]


Sigmund implements several techniques to be a helpful assistant that provides useful answers.


## Step 1: Documentation search

If *Use documentation* is enabled (in the menu), then, before answering a user question, Sigmund searches for relevant sections in the documentation, which are by default related to [OpenSesame](https://osdoc.cogsci.nl/) and [DataMatrix](https://pydatamatrix.eu). 

Unlike most documentation-enabled chatbots, Sigmund does not simply perform a vector search to retrieve documents that are similar to the question. Instead, Sigmund formulates a number of search queries that are used to perform a vector search. Once a set of seemingly relevant documents have been retrieved, each of them is evaluated to determine whether it is indeed relevant to the user question. If not, the document is discarded.

The documentation-search phase consists of several steps, which may sound time-consuming and expensive. However, it is performed with a cheap and fast model (by default GPT 3.5 turbo), which keeps it manageable.


## Step 2: Question answering

Relevant documents (if any) are subsequently included in the system prompt (context), so that Sigmund is able to provide accurate answers about things that it does not know very well. Because of this, Sigmund is much better at answering questions about OpenSesame and DataMatrix than other chatbots are.

Sigmund is also able to do the following:

- Search for scientific articles on Google Scholar
- Execute Python and R code
- Download files and web pages and store them as attachments
- Read attachments

Sigmund does this by including specific JSON syntax (hidden from the user) in its reply. When a JSON command is detected in a reply, the corresponding tool is executed, and the result of the tool is included in the conversation in the form of an AI message. Sigmund continues to reply and execute tools until it feels that its reply is finished.

Question answering is handled by an expensive and slow model (by default GPT 4 turbo) for the highest quality.


## How can I get an account?

Sigmund is currently in limited beta and by invitation only. If you have received an invitation, you can log in using your account from <https://forum.cogsci.nl/>. 


## Privacy

Sigmund encrypts all messages and attachments using a key that is based on your password. This means that no-one, including the system administrators, can read your messages.

By default, Sigmund uses the large-language-model API provided by OpenAI. OpenAI does not use data that they receive through the API for any purposes other than replying to the request. Notably, your data will not be used to train their models. For more information, see their terms of service:

- <https://openai.com/enterprise-privacy>
