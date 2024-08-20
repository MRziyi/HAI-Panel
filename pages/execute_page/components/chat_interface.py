import asyncio
import json
import time
import param
import panel as pn

from panel.viewable import Viewer

from pages.execute_page.components.agents import print_formatted_message
import global_vars
from pages.execute_page.components.stt_engine import STTEngine

pn.extension()  # for notebook

class ChatInterface(Viewer):
    messages = param.List(doc="A list of messages.", default=[
        {"content": "System Initialized", "name": "System"},
    ])
    agents = param.List(doc="A list of agents.")

    def chat_send(self,event):
        text=self.text_input.value
        if(text==''):
            return
        self.text_input.value=""
        self.add_message(text,"User")
        if global_vars.input_future and not global_vars.input_future.done():
            global_vars.input_future.set_result(text)
        else:
            global_vars.chat_task.cancel()  # 取消任务
            user_proxy = global_vars.groupchat.agent_by_name("Admin")
            global_vars.chat_task = asyncio.create_task(user_proxy.a_initiate_chat(recipient=global_vars.groupchat_manager, message=text, clear_history=False))
            

    def chat_import(self,event):
        try:
            with open('chat_history/chat_history.txt', 'r') as f:  # 使用 'r' 模式读取文件
                text = f.read()
            results = json.loads(text)
            self.content=''
            self.messages.clear()
            # 遍历列表中的每个元素，并调用 send_chat_message 函数
            for message in results:
                time.sleep(0.1)
                print_formatted_message("x", message)
            self.add_message("Chat history imported!", name="System")
            last_agent, last_message=global_vars.groupchat_manager.resume(results,remove_termination_string='')
            global_vars.chat_task = asyncio.create_task(last_agent.a_initiate_chat(recipient=global_vars.groupchat_manager, message=last_message, clear_history=False))
        except FileNotFoundError:
            self.add_message("Chat history file not found!", name="System")
        except json.JSONDecodeError:
            self.add_message("Error decoding chat history!", name="System")


    def chat_export(self,event):
        try:
            with open('chat_history/chat_history.txt', 'w') as f:  # 使用 'w' 模式写入文件
                f.write(json.dumps(global_vars.groupchat.messages, indent=4))  # 使用缩进格式化输出
            self.add_message("Chat history exported!",name="System")
        except Exception as e:
            self.add_message(f"Error exporting chat history: {e}",name="System")

    def __init__(self, **params):
        super().__init__(**params)
        self.avatars= {agent["name"]: agent["avatar"] for agent in self.agents}
        self.avatars["System"] = "⚙️"
        self.avatars["Admin"] = "👨🏻‍💼"
        self.avatars["User"] = "😉"
        self._markdown = pn.pane.Markdown(sizing_mode='stretch_both')

        self.refresh_messages()

        self.text_input = pn.widgets.TextAreaInput(width=320, placeholder="Chat with agents",)
        send_button = pn.widgets.Button(button_type='primary', icon="send")
        send_button.on_click(self.chat_send)
        export_button = pn.widgets.Button(icon="file-arrow-right",button_type='warning')
        export_button.on_click(self.chat_export)
        import_button = pn.widgets.Button(icon="file-arrow-left",button_type='success')
        import_button.on_click(self.chat_import)
        start_stop_button = pn.widgets.Button(name='开始识别', button_type='primary', width=250)
        stt_engine = STTEngine(start_stop_button, self.text_input)
        start_stop_button.on_click(stt_engine.start_stop_recognition)
        start_stop_button.on_click(self.chat_send)

        input_text_layout = pn.Row(self.text_input, send_button)
        input_function_layout = pn.Row(start_stop_button,export_button, import_button)
        input_layout = pn.Column(input_text_layout,input_function_layout)
        
        chat_card_content = pn.Column(
            self._markdown,
            sizing_mode='stretch_both',
            scroll=True
        )
        chat_card = pn.Card(chat_card_content, title='Chat With Agents', width=400)
        input_card = pn.Card(input_layout, collapsible=False,hide_header=True, margin=(10,0),width=400,height=110)

        self._layout = pn.Column(chat_card,input_card)

    def __panel__(self):
        return self._layout

    def refresh_messages(self):
        self.content=""
        for message in self.messages:
            name = message.get("name")
            self.content += f"## {self.avatars.get(name)} {name}\n"
            self.content += message["content"] + "\n\n---\n\n"
        self._markdown.object = self.content

    def add_message(self, content,name):
        self.messages.append({'content':content,'name':name})
        self.content += f"## {self.avatars.get(name)} {name}\n"
        self.content += content+ "\n\n---\n\n"
        self._markdown.object = self.content