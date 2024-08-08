import asyncio
import json
import re
import panel as pn
import param

import global_vars

class StepList(pn.viewable.Viewer):
    agents = param.List(doc="A list of agents.")
    steps = param.List(doc="A list of tasks.")
    task_name =param.String(doc="Name of task")
    task_req = param.String(doc="Requirements of task")
    
    
    def __init__(self, **params):
        super().__init__(**params)
        self._layout = pn.Column(
            pn.pane.GIF('https://upload.wikimedia.org/wikipedia/commons/b/b1/Loading_icon.gif', sizing_mode='stretch_width'),
            "正在推荐合适的步骤..."
            )
        asyncio.create_task(self.generate_step_list())

    async def generate_step_list(self):
        raw_step_list = await global_vars.global_assistant.a_generate_reply(messages=[{
        "role": "user",
        "name": "Admin",
        "content": f'''你需要为<task>标签内的任务推荐一个合适的步骤，给各个步骤分配<agents>标签内的Agents，
参考<example_task>标签的样例任务，以给出<example_output>标签内样例输出的格式进行回复，只需要回复json格式即可
<task>{self.task_name}: {self.task_req}</task>
<agents>{self.agents}</agents>'''+
'''
<example_task>行程规划：我需要带领4人的团队前往东南大学参加学术会议，同时在南京知名景点参观。你需要考虑时间安排、交通、资金等全面的因素，并且每个团队成员有着不同的喜好和倾向。请权衡内容，制定平衡合理的**观光景点安排**</example_task>
<example_output>
[
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
]
</example_output>'''
    }])
        # 使用正则表达式提取 JSON 内容
        json_pattern = re.compile(r'```json\n(.*?)```', re.DOTALL)
        json_match = json_pattern.search(raw_step_list)
        if json_match:
            json_content = json_match.group(1)
            try:
                self.steps = json.loads(json_content)
            except json.JSONDecodeError as e:
                self._layout.clear()
                self._layout = pn.Column(f"解析失败：\n原始输出：\n{raw_step_list}\n错误：{e}")
        self.update_step_list()

    def get_lists(self):
        return self.agents,self.steps

    def update_step_list(self):
        self._layout.clear()
        for idx, step in enumerate(self.steps):
            step_info = f'## {idx+1}. {step["name"]}\n'
            step_info += step["content"] + "\n\n---\n\n"
            edit_button = pn.widgets.Button(name="Edit")
            edit_button.on_click(lambda event, idx=idx: self.open_edit_modal(idx))
            
            step_panel = pn.Row(pn.pane.Markdown(step_info,width=290), edit_button)
            self._layout.append(step_panel)
        
        add_step_button = pn.widgets.Button(name='Add Step')
        add_step_button.on_click(self.open_add_modal)
        self._layout.append(add_step_button)
        
    def open_edit_modal(self, idx):
        def confirm_update(event):
            self.steps[idx] = {
                "name": name_input.value,
                "content": content_input.value
            }
            self.update_step_list()
            global_vars.app.close_modal()

        step = self.steps[idx]
        name_input = pn.widgets.TextInput(name="步骤名", value=step["name"])
        content_input = pn.widgets.TextInput(name="步骤内容", value=step["content"])
        confirm_button = pn.widgets.Button(name="Confirm Edit", button_type='primary')
        delete_button = pn.widgets.Button(name="Delete", button_type='danger')
        delete_button.on_click(lambda event, idx=idx: self.delete_step(idx))
        
        confirm_button.on_click(confirm_update)
        modal_content = pn.Row(name_input, content_input)
        buttons = pn.Row(confirm_button, delete_button)
        global_vars.modal_content[:] = [modal_content,buttons]
        global_vars.app.open_modal()


        
    def open_add_modal(self, event):
        name_input = pn.widgets.TextInput(name="Name", value="")
        avatar_input = pn.widgets.TextInput(name="Avatar", value="")
        system_message_input = pn.widgets.TextAreaInput(name="System Message", value="")
        confirm_button = pn.widgets.Button(name="Confirm Add", button_type='primary')
        
        def confirm_add(event):
            self.steps.append({
                "name": name_input.value,
                "content": content_input.value
            })
            self.update_step_list()
            global_vars.app.close_modal()
        
        name_input = pn.widgets.TextInput(name="步骤名")
        content_input = pn.widgets.TextInput(name="步骤内容")
        confirm_button.on_click(confirm_add)
        modal_content = pn.Row(name_input, content_input)
        global_vars.modal_content[:] = [modal_content,confirm_button]
        global_vars.app.open_modal()

    def delete_step(self, idx):
        global_vars.app.close_modal()
        self.steps.pop(idx)
        self.update_step_list()

    def __panel__(self):
        return self._layout