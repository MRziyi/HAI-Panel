# To install required packages:
# pip install pyautogen==0.2.9 panel==1.3.8
import json
import autogen

import panel as pn
import asyncio
import global_vars
from autogen import register_function
from tools import human_feedback_tool


def print_messages(recipient, messages, sender, config):
    print(f"Messages from: {sender.name} sent to: {recipient.name} | num messages: {len(messages)} | message: {messages[-1]}")
    content = messages[-1]['content']
    try:
        data = json.loads(content)
        md_content = data.get('content', '')  # 从 JSON 中获取 'content' 字段
        chat_content = data.get('chat')  # 从 JSON 中获取 'chat' 字段
    except json.JSONDecodeError:
        # 如果解析失败，则将 content 视为普通字符串
        md_content = None
        chat_content = None
    if(md_content):
        global_vars.markdown_display.object = md_content
    if all(key in messages[-1] for key in ['name']):
        global_vars.chat_interface.send(f'@{recipient.name}, '+(chat_content or md_content or content), user=messages[-1]['name'], avatar=global_vars.avatars[messages[-1]['name']], respond=False)
    else:
        global_vars.chat_interface.send(chat_content or md_content or content, user=recipient.name, avatar=global_vars.avatars[recipient.name], respond=False)
    
    return False, None  # required to ensure the agent communication flow continues

class MyConversableAgent(autogen.ConversableAgent):

    async def a_get_human_input(self, prompt: str) -> str:
        print('--getting human input--')  # or however you wish to display the prompt
        global_vars.chat_interface.send(prompt, user="System", respond=False)
        # Create a new Future object for this input operation if none exists
        if global_vars.input_future is None or global_vars.input_future.done():
            global_vars.input_future = asyncio.Future()

        # Wait for the callback to set a result on the future
        await global_vars.input_future

        # Once the result is set, extract the value and reset the future for the next input operation
        input_value = global_vars.input_future.result()
        global_vars.input_future = None
        return input_value

class SightseeingPlanAgents():
    def __init__(self) -> None:
        self.llm_config=global_vars.llm_config
        pass

    def user_proxy(self) -> MyConversableAgent:
        m_user_proxy = MyConversableAgent(
            name="Admin",
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("exit"),
            system_message="""你是人类Admin，与Planner讨论计划，计划的执行需要被Admin批准
        重点：
        - 请使用中文与用户交互。
        - 用户可以指定其他Agent接手任务或是讨论，当用户提出类似要求时应该立刻满足他。
        - 为了方便用户阅读，你的输出可以是以下两种格式：
            1. 当你的输出包含具体的任务内容/计划时，你**必须**严格按照下面列出的“输出格式1”
                输出格式1：
                - 你的输出应该是**一份**json格式的输出，应该包括content与chat两部分，content是较长或较完整或较详细的任务内容/提议/计划，chat是较短的自己的想法或是下一步的计划，例子如下：
                {
                    "content":"# 具体的长内容，比如某个方案，使用Markdown格式",
                    "chat":"较短的自己的想法、或是下一步的计划"
                }
            2. 当你的输出内容很短，或不包括具体的任务内容/计划时，你可以直接输出
            """,
            #Only say APPROVED in most cases, and say exit when nothing to be done further. Do not say others.
            code_execution_config=False,
            #default_auto_reply="Approved", 
            human_input_mode="ALWAYS",
            #llm_config=gpt4_config,
        )
        m_user_proxy.register_reply(
            [autogen.Agent, None],
            reply_func=print_messages, 
            config={"callback": None},
        )
        return m_user_proxy

    
    def planner(self) -> autogen.AssistantAgent:
        m_planner = autogen.AssistantAgent(
            name="Planner",
            human_input_mode="NEVER",
            system_message='''你是Planner，提出一个计划，根据Admin与Critic的反馈修改计划，直到Admin批准。
        计划可以涉及Sightseeing Agent（负责规划活动和游览）与Financial Agent（负责预算分配和控制）
        首先解释计划，清楚地列出计划中每一步分别需要谁来参与

        重点：
        - 为了方便用户阅读，你的输出可以是以下两种格式：
            1. 当你的输出包含具体的任务内容/计划时，你**必须**严格按照下面列出的“输出格式1”
                输出格式1：
                - 你的输出应该是**一份**json格式的输出，应该包括content与chat两部分，content是较长或较完整或较详细的任务内容/提议/计划，chat是较短的自己的想法或是下一步的计划，例子如下：
                {
                    "content":"# 具体的长内容，比如某个方案，使用Markdown格式",
                    "chat":"较短的自己的想法、或是下一步的计划"
                }
            2. 当你的输出内容很短，或不包括具体的任务内容/计划时，你可以直接输出
        ''',
            llm_config=self.llm_config,
        )
        m_planner.register_reply(
            [autogen.Agent, None],
            reply_func=print_messages, 
            config={"callback": None},
        )
        return m_planner
    
    def critic(self) -> autogen.AssistantAgent:
        m_critic = autogen.AssistantAgent(
            name="Critic",
            system_message="""你是Critic，需要再次检查其他Agent给出的任务计划、任务结果，并提出反馈

        重点：
        - 为了方便用户阅读，你的输出可以是以下两种格式：
            1. 当你的输出包含具体的任务内容/计划时，你**必须**严格按照下面列出的“输出格式1”
                输出格式1：
                - 你的输出应该是**一份**json格式的输出，应该包括content与chat两部分，content是较长或较完整或较详细的任务内容/提议/计划，chat是较短的自己的想法或是下一步的计划，例子如下：
                {
                    "content":"# 具体的长内容，比如某个方案，使用Markdown格式",
                    "chat":"较短的自己的想法、或是下一步的计划"
                }
            2. 当你的输出内容很短，或不包括具体的任务内容/计划时，你可以直接输出
            """,
            llm_config=self.llm_config,
            human_input_mode="NEVER",
        )
        m_critic.register_reply(
            [autogen.Agent, None],
            reply_func=print_messages, 
            config={"callback": None},
        )
        return m_critic
        

    def financial_agent(self) -> autogen.AssistantAgent:
        m_financial_agent= autogen.AssistantAgent(
            name='FinancialAgent',
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            system_message='''
            你是负责预算分配和控制的财务代理。
            你的主要任务是确保总支出不超出分配的预算。
            你需要审查方案是否可行合理。
            你必须细致地计划和监控支出，并做出必要的调整，以保持在财务限额之内

        重点：
        - 请使用中文与用户交互。
        - 你被**禁止**一次性完成计划，你**必须**在每次回复后通过Admin向用户提问，确保在进行计划之前获得足够详细的信息，进行计划时应与用户逐步讨论进行。
        - 规划过程中面对多个可选项时，你不能自己决定，应该询问用户的意见。
        - 在与用户讨论方案时，你应该提出具有启发性的细节问题，因为用户也不清楚自己想要什么，你需要帮助他找到他想要的安排，例如：对解决问题需要补充的细节信息、用户可能忽略的需求等。
        - 用户可以指定其他Agent接手任务或是讨论，当用户提出类似要求时应该立刻满足他。
        - 为了方便用户阅读，你的输出可以是以下两种格式：
            1. 当你的输出包含具体的任务内容/计划时，你**必须**严格按照下面列出的“输出格式1”
                输出格式1：
                - 你的输出应该是**一份**json格式的输出，应该包括content与chat两部分，content是较长或较完整或较详细的任务内容/提议/计划，chat是较短的自己的想法或是下一步的计划，例子如下：
                {
                    "content":"# 具体的长内容，比如某个方案，使用Markdown格式",
                    "chat":"较短的自己的想法、或是下一步的计划"
                }
            2. 当你的输出内容很短，或不包括具体的任务内容/计划时，你可以直接输出
            ''',
        )
        m_financial_agent.register_reply(
            [autogen.Agent, None],
            reply_func=print_messages, 
            config={"callback": None},
        )
        return m_financial_agent
    

    def sightseeing_agent(self) -> autogen.AssistantAgent:
        m_sightseeing_agent = autogen.AssistantAgent(
            name='SightseeingAgent',
            llm_config=self.llm_config,
            human_input_mode="NEVER",
            system_message='''
            你是负责规划活动和游览的观光代理。
            您的任务是根据团队成员的兴趣安排参观和活动。
            你必须确保为每个人安排参与性强、令人满意的活动，创造难忘的体验。
            请确保观光日程与会议日程不冲突。

        重点：
        - 请使用中文与用户交互。
        - 你被**禁止**一次性完成计划，你**必须**在每次回复后通过Admin向用户提问，确保在进行计划之前获得足够详细的信息，进行计划时应与用户逐步讨论进行。
        - 规划过程中面对多个可选项时，你不能自己决定，应该询问用户的意见。
        - 在与用户讨论方案时，你应该提出具有启发性的细节问题，因为用户也不清楚自己想要什么，你需要帮助他找到他想要的安排，例如：对解决问题需要补充的细节信息、用户可能忽略的需求等。
        - 用户可以指定其他Agent接手任务或是讨论，当用户提出类似要求时应该立刻满足他。
        - 为了方便用户阅读，你的输出可以是以下两种格式：
            1. 当你的输出包含具体的任务内容/计划时，你**必须**严格按照下面列出的“输出格式1”
                输出格式1：
                - 你的输出应该是**一份**json格式的输出，应该包括content与chat两部分，content是较长或较完整或较详细的任务内容/提议/计划，chat是较短的自己的想法或是下一步的计划，例子如下：
                {
                    "content":"# 具体的长内容，比如某个方案，使用Markdown格式",
                    "chat":"较短的自己的想法、或是下一步的计划"
                }
            2. 当你的输出内容很短，或不包括具体的任务内容/计划时，你可以直接输出
            ''',
        )
        m_sightseeing_agent.register_reply(
            [autogen.Agent, None],
            reply_func=print_messages, 
            config={"callback": None},
        )
        return m_sightseeing_agent