import json
import re
from typing import Literal, Union
import autogen
import asyncio

import panel as pn
import global_vars


class MyConversableAgent(autogen.ConversableAgent):
    async def a_get_human_input(self, prompt: str) -> str:
        
        print('--getting human input--')  # or however you wish to display the prompt
        global_vars.chat_interface.add_message("请回答Agent对您的提问以继续", "System")
        # Create a new Future object for this input operation if none exists
        if global_vars.input_future is None or global_vars.input_future.done():
            global_vars.input_future = asyncio.Future()

        # Wait for the callback to set a result on the future
        await global_vars.input_future

        # Once the result is set, extract the value and reset the future for the next input operation
        input_value = global_vars.input_future.result()
        global_vars.input_future = None
        return input_value

def print_message_callback(recipient, messages, sender, config):
    if "callback" in config and  config["callback"] is not None:
        callback = config["callback"]
        callback(sender, recipient, messages[-1])
    last_message = messages[-1]
    sender_name = last_message.get('name',None) or recipient.name
    print(f"Messages from: {sender_name} sent to: {recipient.name} | num messages: {len(messages)} | message: {last_message}")
    if(sender_name=="Critic" or sender_name=="ProcessManager"or sender_name=="Admin"):
        print_formatted_message(recipient.name, last_message)
    else:
        asyncio.create_task(format_and_print_message(recipient.name, last_message))
    return False, None

def print_formatted_message(recipient_name, message):
    content = message.get('content', '')
    sender_name = message.get('name', None) or recipient_name
    json_pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
    json_match = json_pattern.search(content)
    if json_match:
        json_content = json_match.group(1)
    else:
        json_content = content
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        print("----------Failed to decode JSON:--------\n", e)
        print(f"Content: {content}\n-----------------\n")
        data = {}
    
    chat_content = data.get('chat', None)
    current_step = data.get('current_step', None)
    md_content = data.get('content', None)
    if md_content and md_content!="None":
        global_vars.markdown_display.object = md_content

    if current_step:
        global_vars.progress_indicator.current_task = current_step

    message_content = chat_content or content
    global_vars.chat_interface.add_message(
        f'@{recipient_name}, {message_content}' if 'name' in message else message_content,
        name=sender_name,
    )

async def format_and_print_message(recipient_name, message):
    original_content=global_vars.markdown_display.object
    global_vars.markdown_display.object="正在格式化"
    content = message.get('content', '')
    sender_name = message.get('name', None) or recipient_name
    formatted_reply = await global_vars.global_formatter.a_generate_reply(messages=[{
        "role": "user",
        "name": "Admin",
        "content": f'''<content>标签内是待格式化的内容，<format>标签内是目标格式
<content>
{content}
</content>'''+'''
<format>
{
    "chat":"<content>中的提问、较短的想法、或是下一步的打算"
    "content":"<content>中具体的长内容，比如某个长或较完整或较详细的任务内容/提议/计划，使用markdown格式，注意控制字符使用如“\\n”。如果这个参数的内容小于5个句子，则输出None",
}
- 你**只能**使用chat与content参数，你**禁止**自己编撰其他参数
- 你**只能**输出一个json
- 你必须忠实地还原<content>标签内的信息，不能额外添加或编写<content>标签内没有的信息，也不能省略任何给出的信息。
</format>'''
    }])
    # 使用正则表达式提取 JSON 内容
    json_pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
    json_match = json_pattern.search(formatted_reply)
    if json_match:
        json_content = json_match.group(1)
    else:
        json_content = formatted_reply
    try:
        data = json.loads(json_content)
        # try:
        #     index=global_vars.groupchat.messages.index(message)
        # except:
        #     print("IN INDEX EXCEPT")
        #     index=-1
        # print("---------['content']")
        # print(global_vars.groupchat.messages[index]['content'])
        # global_vars.groupchat.messages[index]['content']=json_content
        # print("---------#['content']")
        # print(global_vars.groupchat.messages[index]['content'])
    except json.JSONDecodeError as e:
        print("----------Failed to decode JSON:--------\n", e)
        print(f"Content: {content}\n-----------------\n")
        data = {}

    chat_content = data.get('chat', None)
    md_content = data.get('content', None)
    if md_content and md_content!="None":
        global_vars.markdown_display.object = md_content
    else:
        global_vars.markdown_display.object = original_content

    message_content = chat_content or content

    global_vars.chat_interface.add_message(
        f'@{recipient_name}, {message_content}' if 'name' in message else message_content,
        name=sender_name,
    )

def custom_speaker_selection_func(
    last_speaker: autogen.Agent, 
    groupchat: autogen.GroupChat
) -> Union[autogen.Agent, Literal['auto', 'manual', 'random' 'round_robin'], None]:
    print('------custom_speaker_selection------')
    agents=groupchat.agents
    roles = [agent.name+": "+agent.description for agent in agents]
    agentlist = [agent.name for agent in agents]

    filtered_roles = [role for role in roles if "Admin: " not in role]
    filtered_agentlist = [agent for agent in agentlist if agent != "Admin"]

    if(last_speaker.name=="Admin"):
        agent_name = global_vars.speaker_selector.generate_reply(messages=[{
        "role": "user",
        "name": "Admin",
        "content": f'''<role_info>
{filtered_roles}
</role_info>

<message>
{groupchat.messages[-1]}
</message>

<role_list>
{filtered_agentlist}
</role_list>
'''}])
    else:
        agent_name = global_vars.speaker_selector.generate_reply(messages=[{
        "role": "user",
        "name": "Admin",
        "content": f'''<role_info>
{roles}
</role_info>

<message>
{groupchat.messages[-1]}
</message>

<role_list>
{agentlist}
</role_list>

Note: If the conversation is asking for information or decision, you can only select "Admin"'''}])
        
    print(agent_name)
    next_agent=groupchat.agent_by_name(agent_name)
    if(next_agent is None):
        print("!!!next_agent is None!!! AUTO CHOOSE")
        return 'auto'
    else:
        return next_agent