[TOC]

*Sigmund 3 is in public beta. Play around with it, but expect occassional bugs!*

Sigmund has received a complete make over!


# What's new in Sigmund 3?

[Sigmund 3](https://chat.sigmundai.eu) is based on [LibreChat](https://www.librechat.ai/), a mature, open-source, and user-friendly chat interface. By building on LibreChat, we can focus on developing the functionality that make Sigmund unique: privacy and integration with scientific tools and resources, such as OpenSesame (for developing psychology experiments), Sigmund Analyst (for data analysis with Python), OpenAlex (for literature search), and JASP (for statistical analysis).

For now, Sigmund 2 is still the default chat interface available at [sigmundai.eu](https://sigmundai.eu). To use Sigmund 3, visit [chat.sigmundai.eu](https://chat.sigmundai.eu).


# Important change: encryption

Unlike previous versions, Sigmund 3 does *not* fully encrypt user data. The reason is that encryption is currently not implemented in LibreChat, which is the software that Sigmund 3 is based on. This does not mean that your data is unsafe. However, it does mean that someone with administrator access to the server could in principle read your chat history. (The same is true for almost every other chat bot.)

For now, if full encryption is important, use Sigmund 2, which will remain available at [sigmundai.eu](https://sigmundai.eu).

In the meantime, we are working to implement full encryption also in Sigmund 3!


# How to connect an application to Sigmund 3

(First, enable Sigmund 3 in your application as explained below.)

Log into [chat.sigmundai.eu](https://chat.sigmundai.eu). Click the + button below the chat box to reveal the tool menu. Select the "Get Pairing Code" tool. Now ask Sigmund for a pairing code: "Hi Sigmund, can you give me a pairing code?"

Now switch to OpenSesame or Sigmund Analyst. Click on the Sigmund icon in the toolbar to reveal the Sigmund widget. Click "Connect" and enter the pairing code.

Sigmund 3 is now connected to OpenSesame or Sigmund Analyst!


# How to enable Sigmund 3 in Sigmund Analyst

Requires Sigmund Analyst version 1.3.0 or higher.

Click the gear icon in the toolbox to reveal the settings. Under "Sigmund 3", enable "Sigmund Mcp Relay Enabled". Close and restart the application. Sigmund 3 is now enabled!


# How to enable Sigmund 3 in OpenSesame

TODO


# How to enable Sigmund 3 in JASP

TODO
