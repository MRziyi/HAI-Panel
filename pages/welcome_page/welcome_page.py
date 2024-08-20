import json
import panel as pn
import param
import autogen
import global_vars
from pages.config_page.config_page import ConfigPage
from pages.execute_page.components.agents import MyConversableAgent, print_message_callback
from pages.execute_page.components.chat_interface import ChatInterface
from pages.execute_page.components.process_indicator import ProcessIndicator
from pages.execute_page.execute_page import ExecutePage


class WelcomePage(pn.viewable.Viewer):

    def switch_to_config_page(self,event):
        config_page = ConfigPage(task_name=self.text_input.value)
        global_vars.app_layout[:] = [config_page]  # 更新布局为 config 页面

    def import_to_execute_page(self,event):
        try:
            with open('config/sightseeing_config.txt', 'r') as f:  # 使用 'r' 模式读取文件
                text = f.read()
            results = json.loads(text)
            task_name = results.get("task_name")
            task_req = results.get("task_req")
            agent_list = results.get("agent_list")
            step_list = results.get("step_list")
        
            print('-------agent_list-------')
            print(agent_list)
            print('-------step_list-------')
            print(step_list)
        except FileNotFoundError:
            print("Chat history file not found!")
        except json.JSONDecodeError:
            print("Error decoding chat history!")

        execute_page = ExecutePage(agents=agent_list,steps=step_list,task_name=task_name,task_req=task_req)
        global_vars.app_layout[:] = [execute_page]
    
    def __init__(self, **params):
        self.text_input = pn.widgets.TextInput(name='请问您想解决什么问题？',value="行程规划")
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')

        # 绑定按钮点击事件
        confirm_button.on_click(self.switch_to_config_page)

        import_button = pn.widgets.Button(icon="file-arrow-left",name="Import Config",button_type='success')
        import_button.on_click(self.import_to_execute_page)

        # 初始布局为 welcome 页面
        global_vars.app_layout[:] = ['# 欢迎来到 POLARIS',
            pn.Row(
                self.text_input,
                confirm_button,
                import_button
            )]
    