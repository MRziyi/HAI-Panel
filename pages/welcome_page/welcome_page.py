import panel as pn
import param
import autogen
import global_vars
from pages.config_page.config_page import ConfigPage
from pages.execute_page.components.agents import MyConversableAgent, print_message_callback
from pages.execute_page.components.chat_interface import ChatInterface
from pages.execute_page.components.process_indicator import ProcessIndicator


class WelcomePage(pn.viewable.Viewer):
    
    def __init__(self, **params):
        def switch_to_config_page(event):
            config_page = ConfigPage(task_name=text_input.value)
            global_vars.app_layout[:] = [config_page]  # 更新布局为 config 页面

        text_input = pn.widgets.TextInput(name='请问您想解决什么问题？')
        confirm_button = pn.widgets.Button(name='确认', button_type='primary')

        # 绑定按钮点击事件
        confirm_button.on_click(switch_to_config_page)

        # 初始布局为 welcome 页面
        global_vars.app_layout[:] = ['# 欢迎来到 POLARIS',
            pn.Row(
                text_input,
                confirm_button,
            )]
    