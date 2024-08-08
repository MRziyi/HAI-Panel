import json
import autogen
import asyncio
import global_vars


def print_message_callback(recipient, messages, sender, config):
    last_message = messages[-1]
    sender_name = last_message.get('name')
    print(f"Messages from: {sender_name} sent to: {recipient.name} | num messages: {len(messages)} | message: {last_message}")
    print_message(recipient.name, last_message)
    return False, None  # 确保代理通信流程继续

def print_message(recipient_name, message):
    content = message.get('content', '')
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print("----------Failed to decode JSON:--------\n", e)
        print(f"Content: {content}\n-----------------\n")
        data = {}
    chat_content = data.get('chat', None)
    md_content = data.get('content', None)
    current_task = data.get('current_step', None)

    if md_content and md_content!="None":
        global_vars.markdown_display.object = md_content

    if current_task:
        global_vars.progress_indicator.current_task = current_task

    sender_name = message.get('name', '')
    message_content = chat_content or content

    global_vars.chat_interface.add_message(
        f'@{recipient_name}, {message_content}' if 'name' in message else message_content,
        name=sender_name,
    )
    
class MyConversableAgent(autogen.ConversableAgent):
    async def a_get_human_input(self, prompt: str) -> str:
        if(global_vars.is_interrupted):
            content = global_vars.is_interrupted
            global_vars.is_interrupted=None
            return content
        
        print('--getting human input--')  # or however you wish to display the prompt
        global_vars.chat_interface.add_message(prompt, "System")
        # Create a new Future object for this input operation if none exists
        if global_vars.input_future is None or global_vars.input_future.done():
            global_vars.input_future = asyncio.Future()

        # Wait for the callback to set a result on the future
        await global_vars.input_future

        # Once the result is set, extract the value and reset the future for the next input operation
        input_value = global_vars.input_future.result()
        global_vars.input_future = None
        return input_value