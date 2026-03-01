# """
# Minimal FastAPI wrapper that mounts Chainlit at /chat.
# This ensures Chainlit generates correct asset paths (/chat/assets/...)
# when served behind nginx at the /chat subpath.
# """

# import os

# from chainlit.utils import mount_chainlit
# from fastapi import FastAPI

# app = FastAPI()

# _agent_path = os.path.join(os.path.dirname(__file__), "agent.py")
# mount_chainlit(app=app, target=_agent_path, path="/chat")
