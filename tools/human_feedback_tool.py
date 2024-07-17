import time
import global_vars
from pydantic import BaseModel, Field
from typing import Annotated


class HumanFeedbackInput(BaseModel):
    question: Annotated[str, Field(description="The question that needs feedback from human")]


def human_feedback_tool(input: Annotated[HumanFeedbackInput, "Input to the Human Feedback Tool."]) -> str:

    # chat_interface = global_vars.chat_interface
    # chat_interface.send(question, user="assistant", respond=False)
    while global_vars.user_input == None:
        time.sleep(1)  

    human_comments = global_vars.user_input
    global_vars.user_input = None

    return human_comments