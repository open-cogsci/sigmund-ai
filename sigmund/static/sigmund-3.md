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

## OpenSesame

Ensure that you are using `opensesame-extension-sigmund` version 1.5.0 or higher. Update through the automatic updater, or run:

```
pip install opensesame-extension-sigmund pyqt_code_editor sigmund-mcp-relay --upgrade
```

Next:

1. Start OpenSesame.
2. Open Tools → Preferences → Advanced Settings. Under SigmundMcpRelay, enable sigmund_mcp_relay_enabled.
3. Restart OpenSesame.
4. Open a browser and visit [chat.sigmundai.eu](https://chat.sigmundai.eu).
5. Click the + button below the chat box and activate "Get Pairing Code".
6. Ask for a pairing code. ("Hi Sigmund, can you give me a pairing code?")
7. Switch back to OpenSesame.
8. Click on the Sigmund icon in the toolbar to reveal the Sigmund widget. Click "Connect" and enter the pairing code.

You are now connected!


## Sigmund Analyst

Requires Sigmund Analyst (`pyqt_code_editor`) version 1.3.0 or higher. To update, run:

```
pip install pyqt_code_editor sigmund-mcp-relay --upgrade
```

Open Sigmund Analyst (the desktop application). Click the gear icon in the toolbox to reveal the settings. Under "Sigmund 3", enable "Sigmund Mcp Relay Enabled". Close and restart the application. Sigmund 3 is now enabled!

Next:

1. Start Sigmund Analyst.
2. Click the gear icon in the toolbox to reveal the settings. Under "Sigmund 3", enable "Sigmund Mcp Relay Enabled". sigmund_mcp_relay_enabled.
3. Restart Sigmund Analyst.
4. Open a browser and visit [chat.sigmundai.eu](https://chat.sigmundai.eu).
5. Click the + button below the chat box and activate "Get Pairing Code".
6. Ask for a pairing code. ("Hi Sigmund, can you give me a pairing code?")
7. Switch back to Sigmund Analyst.
8. Click on the Sigmund icon in the toolbar to reveal the Sigmund widget. Click "Connect" and enter the pairing code.

You are now connected!

## JASP

TODO
