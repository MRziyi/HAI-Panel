This is the backend for the project HAI

To interrupt the chatgroup, you need change source code in AutoGen lib:
* Find autogen/agentchat/groupchat.py
* In async function a_run_chat()
* Change "except KeyboardInterrupt:" to "except asyncio.CancelledError:"