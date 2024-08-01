# To install required packages:
# pip install pyautogen==0.2.9 panel==1.3.8
import json
import re
import autogen

import panel as pn
import asyncio
import global_vars
from autogen import register_function
from tools import human_feedback_tool


def print_message_callback(recipient, messages, sender, config):
    last_message = messages[-1]
    print(f"Messages from: {sender.name} sent to: {recipient.name} | num messages: {len(messages)} | message: {last_message}")
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

    sender_name = message.get('name', recipient_name)
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
class SightseeingPlanAgents():
    def __init__(self) -> None:
        self.llm_config=global_vars.llm_config
        pass

    def user_proxy(self) -> MyConversableAgent:
        m_user_proxy = MyConversableAgent(
            name="Admin",
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("exit"),
            system_message="""你是人类Admin
        重点：
        - 请使用中文与用户交互。
        - 用户可以指定其他Agent接手任务或是讨论，当用户提出类似要求时应该立刻满足他。
        - 为了方便用户阅读，你的输出**必须**严格按照下面列出的“输出格式”
            输出格式：
            - 你的输出应该是**一个**json格式的，应该包括如下例子中的参数：
            {
                "chat":"较短的自己的想法、或是下一步的打算"
            }
            - 你**只能**使用chat参数，你**禁止**自己编撰其他参数
            - 你**只能**输出一个json
            """,
            
            code_execution_config=False,
            #default_auto_reply="Approved", 
            human_input_mode="ALWAYS",
        )
        m_user_proxy.register_reply(
            [autogen.Agent, None],
            reply_func=print_message_callback, 
            config={"callback": None},
        )
        return m_user_proxy

    def critic(self) -> autogen.AssistantAgent:
        m_critic = autogen.AssistantAgent(
            name="Critic",
            system_message="""你是Critic，需要再次检查其他Agent给出的任务计划、任务结果，并提出反馈

        重点：
        - 为了方便用户阅读，你的输出**必须**严格按照下面列出的“输出格式”
            - 你的输出应该是**一个**json格式的，应该包括如下例子中的参数：
            {
                "chat":"较短的自己的想法、或是下一步的打算"
            }
            - 你**只能**使用chat参数，前者用于较短内容，后者只用于较长的内容，你**禁止**自己编撰其他参数
            - 你**只能**输出一个json
        - 当你想向用户提问，或者希望获取更多信息时，请通过Admin向用户提问
            """,
            llm_config=self.llm_config,
            human_input_mode="NEVER",
        )
        m_critic.register_reply(
            [autogen.Agent, None],
            reply_func=print_message_callback, 
            config={"callback": None},
        )
        return m_critic
    

    def process_manager(self) -> autogen.AssistantAgent:
        m_process_manager = autogen.AssistantAgent(
            name="ProcessManager",
            system_message="""你是ProcessManager，负责管理任务执行进度，为Agent分配任务，或通过Admin向用户提问 
            任务步骤：
                {
                    "name":"测试系统",
                    "content":"本步骤是为了让Admin测试系统的各个功能，没有具体的目标，当Admin提出正式开始实验后进入下一步骤"
                },
                {
                    "name":"为不同成员分配景点",
                    "content":"由SightseeingAgent根据用户的需求特点搜索并列出南京的景点，与Admin讨论给成员的景点分配，之后由Critic给出建议并改进"
                },
                {
                    "name":"规划时间表",
                    "content":"由SightseeingAgent根据Step1中的景点分配，参考会议时间安排进行，之后由Critic与Admin给出建议并改进"
                },
                {
                    "name":"列出预算表",
                    "content":"由FinanceAgent根据Step2中的景点选择列出预算表，之后由Critic给出建议并改进"
                },
                {
                    "name":"预算表调整",
                    "content":"由Admin与FinanceAgent和SightseeingAgent根据Step3中的景点选择列出预算表，调整预算与step2的安排，之后由Critic给出建议并改进"
                },
                {
                    "name":"输出观光计划",
                    "content":"输出最后的结果，任务完成"
                }

            重点：
            - 为了方便用户阅读，你的输出**必须**严格按照下面列出的“输出格式”
                输出格式：
                - 你**只能**使用chat与current_step参数，你**禁止**自己编撰其他参数
                {
                    "chat":"较短的自己的想法、或是下一步的打算"
                    "current_step":1 # 当前进行的任务编号
                }
                - 你**只能**输出一个json
                - 你**必须**根据聊天记录判断当前任务进度执行到了哪一步，并通过"current_step"进行表示
            - 当你想向用户提问，或者希望获取更多信息时，请通过Admin向用户提问
            - 在一个任务结束后，你必须向用户提问，直到批准才可以进行下一步
                """,
            llm_config=self.llm_config,
            human_input_mode="NEVER",
        )
        m_process_manager.register_reply(
            [autogen.Agent, None],
            reply_func=print_message_callback, 
            config={"callback": None},
        )
        return m_process_manager
        

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
        - 为了方便用户阅读，你的输出**必须**严格按照下面列出的“输出格式”
            - 你的输出应该是**一个**json格式的，应该包括如下例子中的参数：
            {
                "chat":"较短的自己的想法、或是下一步的打算"
                "content":"用于具体的长内容，比如某个长或较完整或较详细的任务内容/提议/计划，使用markdown格式。如果这个参数的内容小于5个句子，则输出None",
            }
            - 你**只能**使用chat与content参数，你**禁止**自己编撰其他参数
            - 你**只能**输出一个json
            ''',
        )
        m_financial_agent.register_reply(
            [autogen.Agent, None],
            reply_func=print_message_callback, 
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
        - 为了方便用户阅读，你的输出**必须**严格按照下面列出的“输出格式”
            - 你的输出应该是**一个**json格式的，应该包括如下例子中的参数：
            {
                "chat":"较短的自己的想法、或是下一步的打算"
                "content":"用于具体的长内容，比如某个长或较完整或较详细的任务内容/提议/计划，使用markdown格式。如果这个参数的内容小于5个句子，则输出None",
            }
            - 你**只能**使用chat与content参数，你**禁止**自己编撰其他参数
            - 你**只能**输出一个json"
            ''',
        )
        m_sightseeing_agent.register_reply(
            [autogen.Agent, None],
            reply_func=print_message_callback, 
            config={"callback": None},
        )
        return m_sightseeing_agent