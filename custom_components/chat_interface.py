import json
import time
import param
import panel as pn

from panel.viewable import Viewer

from agents import print_message
import global_vars
from stt_engine import STTEngine

pn.extension()  # for notebook


avatars = {
    "FinancialAgent": "💵",
    "SightseeingAgent":"🏜️",
    "Admin":"👨🏻‍💼",
    'ProcessManager':"⏩️",
    'Critic':'📝',
    "User":'😉',
    "System":"⚙️"
}

class ChatInterface(Viewer):
    messages = param.List(doc="A list of messages.", default=[
        {"content": "System Initialized", "name": "System"},
    ])

    def chat_send(self,event):
        text=self.text_input.value
        if(text==''):
            return
        self.text_input.value=""
        self.add_message(text,"User")
        if global_vars.input_future and not global_vars.input_future.done():
            global_vars.input_future.set_result(text)
        else:
            # 如果没有 Agent 在等待用户输入，触发 KeyBoardInterrupt
            global_vars.is_interrupted=self.text_input.value
            global_vars.chat_task.cancel()  # 取消任务
            if global_vars.input_future and global_vars.input_future.done():
                print(f"Canceled! with history:{global_vars.input_future.result()}")
            else: 
                print("Canceled!")

    def chat_import(self,event):
        try:
            with open('chat_history.txt', 'r') as f:  # 使用 'r' 模式读取文件
                text = f.read()
            results = json.loads(text)
            self.content=''
            self.messages.clear()
            # 遍历列表中的每个元素，并调用 send_chat_message 函数
            for message in results:
                time.sleep(0.1)
                print_message("x", message)
            self.add_message("Chat history imported!", name="System")
            global_vars.groupchat_manager.resume(results)
        except FileNotFoundError:
            self.add_message("Chat history file not found!", name="System")
        except json.JSONDecodeError:
            self.add_message("Error decoding chat history!", name="System")


    def chat_export(self,event):
        try:
            with open('chat_history.txt', 'w') as f:  # 使用 'w' 模式写入文件
                f.write(json.dumps(global_vars.groupchat.messages, indent=4))  # 使用缩进格式化输出
            self.add_message("Chat history exported!",name="System")
        except Exception as e:
            self.add_message(f"Error exporting chat history: {e}",name="System")

    def __init__(self, **params):
        super().__init__(**params)
        self._markdown = pn.pane.Markdown(sizing_mode='stretch_both', max_height=380)
        self.refresh_messages()

        self.text_input = pn.widgets.TextAreaInput(width=400)
        send_button = pn.widgets.Button(button_type='primary', icon="send")
        send_button.on_click(self.chat_send)
        export_button = pn.widgets.Button(icon="file-arrow-right",button_type='warning')
        export_button.on_click(self.chat_export)
        import_button = pn.widgets.Button(icon="file-arrow-left",button_type='success')
        import_button.on_click(self.chat_import)
        start_stop_button = pn.widgets.Button(name='开始识别', button_type='primary', width=330)
        stt_engine = STTEngine(start_stop_button, self.text_input)
        start_stop_button.on_click(stt_engine.start_stop_recognition)
        start_stop_button.on_click(self.chat_send)

        input_text_layout = pn.Row(self.text_input, send_button)
        input_function_layout = pn.Row(start_stop_button,export_button, import_button)
        input_layout = pn.Column(input_text_layout,input_function_layout)

        md_card = pn.Card(self._markdown, title='Chat With Agents', styles={'background': 'WhiteSmoke', 'overflow': 'auto'}, width=500, height=840)
        input_card = pn.Card(input_layout, collapsible=False,hide_header=True,styles={'background': 'WhiteSmoke'},width=500,height=110)
        self._layout = pn.Column(md_card,input_card)

    def __panel__(self):
        return self._layout

    def refresh_messages(self):
        self.content=""
        for message in self.messages:
            name = message.get("name")
            self.content += f"## {avatars.get(name)} {name}\n"
            self.content += message["content"] + "\n\n---\n\n"
        self._markdown.object = self.content

    def add_message(self, content,name):
        self.messages.append({'content':content,'name':name})
        self.content += f"## {avatars.get(name)} {name}\n"
        self.content += content+ "\n\n---\n\n"
        self._markdown.object = self.content