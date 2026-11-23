[TOC]

<img src='/static/sigmund-3-preview.png' style="width:100%">

# What's new in Sigmund 3?

*Sigmund 3 is in public beta. Play around with it but expect occassional bugs!*

[Sigmund 3](https://chat.sigmundai.eu) is a complete rewrite based on LibreChat, a mature chat interface. By building on LibreChat, we can focus on the functionality that makes Sigmund unique: privacy and integration with scientific tools and resources.

Right now, Sigmund 3 integrates with the following tools:

- __OpenSesame__ for developing psychology experiments
- __Sigmund Analyst__ for data analysis with Python
- __JASP__ for statistical analysis
- __OpenAlex__ for literature search

Support for the following tools will be rolled out soon:

- __Jupyter Notebook__ for data analysis with Python
- __Positron (formerly RStudio)__ for data analysis with R
- __MindProbe/ JATOS__ for managing online psychology experiments

 
For now, Sigmund 2 is still the default chat interface at [sigmundai.eu](https://sigmundai.eu). To use Sigmund 3, visit [chat.sigmundai.eu](https://chat.sigmundai.eu).


# Important change: encryption

Unlike previous versions, Sigmund 3 does *not* fully encrypt user data. The reason is that encryption is currently not implemented in LibreChat, which is the software that Sigmund 3 is based on. This does not mean that your data is unsafe. However, it does mean that someone with administrator access to the server could in principle read your chat history. (The same is true for almost every other chat bot.)

For now, if full encryption is important, use Sigmund 2, which will remain available at [sigmundai.eu](https://sigmundai.eu). In the meantime, we are working to implement full encryption also in Sigmund 3!


# Supported applications

## Connect to Sigmund 3 (all applications)

Sigmund 3 lives in the cloud and connects to your computer through a bridge (or relay) that is built into OpenSesame and Sigmund Analyst.

This bridge is only available in the most recent software updates. So first make sure you are up to date by running the following command in the Jupyter (Python) console of OpenSesame/ Sigmund Analyst:

```
pip install opensesame-core opensesame-extension-sigmund pyqt_code_editor sigmund-mcp-relay --upgrade
```

Restart OpenSesame/ Sigmund Analyst after the update is complete.

Now click on the Sigmund icon in the toolbar. The Sigmund panel will appear. By default, it still connects to Sigmund 2. Therefore, click "Try out the new Sigmund 3 (beta)!" at the top of the panel. The panel will now switch to Sigmund 3.

In the Sigmund 3 panel, click "Connect". If you haven't connected before, Sigmund now asks for a pairing code.

Now open <a href="https://chat.sigmundai.eu" target="_blank">chat.sigmundai.eu</a> in a browser and log in. Click the + button below the chat box. In the tool menu that appears, click on "Show All" next to MCP SERVERS. In the tool overview that appears, activate "Get Pairing Code". Switch back to the conversation, and ask for a pairing code. ("Hi Sigmund, can you give me a pairing code?")

Switch back to OpenSesame/ Sigmund Analyst and enter the pairing code.

You are now connected!


## OpenSesame

Connect OpenSesame to Sigmund 3 as described above. Activate the "Build Experiments" and/ or "Search OpenSesame documentation" tools in OpenSesame as well as in Sigmund 3.


## Sigmund Analyst

__Important:__ By connecting Sigmund Analyst to Sigmund 3, you provide an AI with (nearly) unrestricted access to your computer.

Connect Sigmund Analyst to Sigmund 3 as described above. Activate the "Execute Code" and/ or "Access Files and Folders" tools in Sigmund Analyst as well as in Sigmund 3. The "Access Files and Folders" tool lets you select a folder that Sigmund 3 can access.


## JASP

In JASP, go to Preferences → Advanced → Remote control and enable the JASP-RPC server. Leave JASP running.

Connect OpenSesame or Sigmund Analyst to Sigmund 3 as described above. Activate the "Perform Statistics with JASP" tool in OpenSesame/ Sigmund Analyst as well as in Sigmund 3.


## Jupyter Notebook

Coming soon!

## Positron (formerly RStudio)

Coming soon!

## MindProbe/ JATOS

Coming soon!
