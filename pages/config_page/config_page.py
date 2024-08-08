import param
import panel as pn

from panel.viewable import Viewer
import global_vars
from pages.config_page.components.agent_list import AgentList
from pages.config_page.components.step_list import StepList
from pages.execute_page.execute_page import ExecutePage

pn.extension()  # for notebook

class ConfigPage(Viewer):
    task_name = param.String()

    def __init__(self, **params):
        super().__init__(**params)

        self.req_input = pn.widgets.TextAreaInput(
            name=f'任务：{self.task_name}', 
            auto_grow=True, 
            max_rows=10, 
            rows=6, 
            placeholder="任务已知的详细信息/要求/约束",
            sizing_mode='stretch_width'
        )

        confirm_button = pn.widgets.Button(name='确认', button_type='primary')
        confirm_button.on_click(self.req_confirm)
        
        self.req_content = pn.Column(
            "## 请输入任务详细信息/要求/约束",
            self.req_input,
            confirm_button
        )
        req_card = pn.Card(self.req_content, title='详细信息', max_width=400)

        self.agent_list_content = pn.Column("# 请首先确认任务的详细信息/要求/约束")
        agent_card = pn.Card(self.agent_list_content, title='Agents分配', margin=(0, 20), max_width=400)

        self.step_list_content = pn.Column("# 请首先确认任务的Agents分配")
        step_card = pn.Card(self.step_list_content, title='步骤配置', max_width=400)

        self._layout = pn.Row(req_card, agent_card, step_card)

    def req_confirm(self, event):
        confirmed_req = f"## 任务「{self.task_name}」的详细信息\n{self.req_input.value}"
        self.req_content[:] = [confirmed_req]
        
        agent_list_content = AgentList(task_name=self.task_name,task_req=self.req_input.value)
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')
        confirm_button.on_click(lambda event, agent_list_content=agent_list_content: self.agents_confirm(agent_list_content))
        
        self.agent_list_content[:] = [agent_list_content, confirm_button]
    
    def agents_confirm(self, agent_list_content):
        agent_list=agent_list_content.get_agents()
        agent_list.insert(0,{"name": "ProcessManager", "avatar": "⏩️", "system_message": "负责管理任务执行进度，为Agent分配任务，或通过Admin向用户提问"})
        agent_list.insert(0,{"name": "Critic", "avatar": "📝", "system_message": "再次检查其他Agent给出的任务计划、任务结果，并提出反馈"})
        confirmed_agents = f"## 任务「{self.task_name}」的Agents分配\n"
        for agent in agent_list:
            confirmed_agents += f'## {agent["avatar"]} {agent["name"]}\n'
            confirmed_agents += agent["system_message"] + "\n\n---\n\n"
        
        step_list_content = StepList(agents=agent_list,task_name=self.task_name,task_req=self.req_input.value)
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')
        confirm_button.on_click(lambda event, step_list_content=step_list_content: self.steps_confirm(step_list_content))
        self.agent_list_content[:] = [confirmed_agents]
        self.step_list_content[:] = [step_list_content, confirm_button]

    
    def steps_confirm(self,step_list_content):
        agent_list,step_list=step_list_content.get_lists()
        step_info = f"## 任务「{self.task_name}」的步骤分配\n"
        for idx, step in enumerate(step_list):
            step_info += f'## {idx+1}. {step["name"]}\n'
            step_info += step["content"] + "\n\n---\n\n"
        
        execute_page = ExecutePage(agents=agent_list,steps=step_list,task_name=self.task_name,task_req=self.req_input.value)
        self.step_list_content[:] = [step_info]
        global_vars.app_layout[:] = [execute_page]

    def __panel__(self):
        return self._layout

