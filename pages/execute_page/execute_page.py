import asyncio
import panel as pn
import param
import autogen
import global_vars
from pages.execute_page.components.agents import MyConversableAgent, custom_speaker_selection_func,print_message_callback
from pages.execute_page.components.chat_interface import ChatInterface
from pages.execute_page.components.process_indicator import ProcessIndicator


class ExecutePage(pn.viewable.Viewer):
    agents = param.List(doc="A list of agents.")
    steps = param.List(doc="A list of tasks.")
    task_name = param.String(doc="Name of task")
    task_req = param.String(doc="Requirements for task")

    def init_agent_list(self) -> list[autogen.Agent]:
        agent_list=[]

        for agent_info in self.agents:
            if(agent_info['name']=="Critic"):
                agent =  autogen.AssistantAgent(
                name="Critic",
                description="你是Critic，需要再次检查其他Agent给出的任务计划、任务结果，并提出反馈",
                system_message="""你是Critic，需要再次检查其他Agent给出的任务计划、任务结果，并提出反馈
            重点：
            - 为了方便用户阅读，你的输出**必须**严格按照下面列出的“输出格式”
                - 你的输出应该是**一个**json格式的，应该包括如下例子中的参数：
                {
                    "chat":"较短的自己的想法、或是下一步的打算"
                }
                - 你**只能**使用chat参数，前者用于较短内容，后者只用于较长的内容，你**禁止**自己编撰其他参数
                - 你**只能**输出一个json
            - 当你想向用户提问，或者希望获取更多信息时，你需要提及关键词“Admin”
            - 当你想与其他Agent交流/委托任务/寻求意见等时，你需要提及它的名字
                """,
                llm_config=global_vars.llm_config,
                human_input_mode="NEVER",
            )
            elif(agent_info['name']=="ProcessManager"):
                agent = autogen.AssistantAgent(
                name="ProcessManager",
                description="你是ProcessManager，负责管理任务执行进度，为Agent分配任务，或通过Admin向用户提问",
                system_message=f'你是ProcessManager，负责管理任务执行进度，为Agent分配任务，或通过Admin向用户提问 \n任务步骤：{self.steps}'+
    """
                重点：
                - 当你想向用户提问，或者希望获取更多信息时，你需要提及关键词“Admin”
                - 当你想与其他Agent交流/委托任务/寻求意见等时，你需要提及它的名字
                - 你**必须**频繁地通过Admin与用户交互
                - 你被**禁止**进行下一个任务，在一个任务结束后，你**必须**向用户提问，直到**批准**才可以进行下一步

                - 为了方便用户阅读，你的输出**必须**严格按照下面列出的“输出格式”
                    输出格式：
                    - 你**只能**使用chat与current_step参数，你**禁止**自己编撰其他参数
                    {
                        "chat":"较短的自己的想法、或是下一步的打算"
                        "current_step":1 (当前进行的任务编号)
                    }
                    - 你**只能**输出一个json
                    - 你**必须**根据聊天记录判断当前任务进度执行到了哪一步，并通过"current_step"进行表示
                    - 在调整"current_step"时，你必须寻求Admin的意见，未经允许的修改将造成严重后果
    """,
                llm_config=global_vars.llm_config,
                human_input_mode="NEVER",
            )
            else:
                agent=autogen.AssistantAgent(
                    name=agent_info['name'],
                    description=f"你是{agent_info['name']}，{agent_info['system_message']}",
                    system_message=f"你是{agent_info['name']}，{agent_info['system_message']}"+
        """
                重点：
                - 请使用中文。
                - 你**必须**频繁地通过Admin与用户交互
                - 当你想向用户提问，或者希望获取更多信息时，你需要提及关键词“Admin”
                - 当你想与其他Agent交流/委托任务/寻求意见等时，你需要提及它的名字
                - 你被**禁止**一次性完成计划，你**必须**在每次回复后通过Admin向用户提问，确保在进行计划之前获得足够详细的信息，进行计划时应与用户逐步讨论进行。
                - 规划过程中面对多个可选项时，你不能自己决定，应该询问用户的意见。
                - 在与用户讨论方案时，你应该提出具有启发性的细节问题，因为用户也不清楚自己想要什么，你需要帮助他找到他想要的安排，例如：对解决问题需要补充的细节信息、用户可能忽略的需求等。
                - 你被**禁止**自行调整任务进度，你必须寻求ProcessManager的意见

""",
                    llm_config=global_vars.llm_config,
                    human_input_mode="NEVER",
                )
            agent.register_reply(
                [autogen.Agent, None],
                reply_func=print_message_callback, 
                config={"callback": None},
            )

            agent_list.append(agent)
        return agent_list
    
    async def initiate_chat(self):

        user_proxy=MyConversableAgent(
            name="Admin",
            # is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("exit"),
            system_message='''你是人类Admin''',
            code_execution_config=False,
            human_input_mode="ALWAYS",
        )
        user_proxy.register_reply(
            [autogen.Agent, None],
            reply_func=print_message_callback, 
            config={"callback": None},
        )
        agent_list = self.init_agent_list()
        agent_list.append(user_proxy)
        print(agent_list)
        global_vars.groupchat = autogen.GroupChat(
            agents=agent_list, 
            speaker_selection_method=custom_speaker_selection_func,
            messages=[])
        global_vars.groupchat_manager = autogen.GroupChatManager(groupchat=global_vars.groupchat,system_message='''Group chat manager. 
重点：
- 你被**禁止**向不同的Agent询问相同的信息
- 当你想向用户提问，或者希望获取更多信息时，请通过Admin向用户提问
''', llm_config=global_vars.llm_config)

        await user_proxy.a_initiate_chat(global_vars.groupchat_manager, message=f"{self.task_name}\n{self.task_req}")


    def __init__(self, **params):
        super().__init__(**params)

        confirmed_agents = f"## 任务「{self.task_name}」的Agents分配\n"
        for agent in self.agents:
            confirmed_agents += f'## {agent["avatar"]} {agent["name"]}\n'
            confirmed_agents += agent["system_message"] + "\n\n---\n\n"
        
        agent_card_content = pn.Column(
            pn.pane.Markdown(confirmed_agents, sizing_mode='stretch_both'),
            sizing_mode='stretch_both',
            max_height=380,
            scroll=True
        )
        
        agent_card = pn.Card(agent_card_content, title='Agents分配', max_height=380, width=350)


        global_vars.progress_indicator = ProcessIndicator(steps=self.steps)
        process_card = pn.Card(global_vars.progress_indicator, title='Process Indicator', sizing_mode='stretch_height',margin=(10,0), width=350)
        info_card = pn.Column(agent_card,process_card)

        global_vars.markdown_display = pn.pane.Markdown("""# Solution""", sizing_mode='stretch_both')
                
        confirm_solution_button = pn.widgets.Button(name="Confirm Solution", button_type='primary', width=80)
        confirm_solution_button.on_click(lambda event, content=global_vars.markdown_display.object: print('---SOLUTION---\n'+content+'\n----SOLUTION----'))
        
        solution_card_content = pn.Column(
            confirm_solution_button,
            global_vars.markdown_display,
            sizing_mode='stretch_both',
            scroll=True
        )
        solution_card = pn.Card(solution_card_content, title='Current Solution', sizing_mode='stretch_height',margin=(0,20), min_width=400, max_width=400)

        global_vars.chat_interface=ChatInterface(agents=self.agents)

        self._layout = pn.Row(info_card, solution_card, global_vars.chat_interface)

        global_vars.chat_task = asyncio.create_task(self.initiate_chat())


    def __panel__(self):
        return self._layout