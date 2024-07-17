import asyncio
import panel as pn
import autogen
from agents import SightseeingPlanAgents
import global_vars
from stt_engine import STTEngine

initiate_chat_task_created = False


async def delayed_initiate_chat(agent, recipient, message):

    global initiate_chat_task_created
    # Indicate that the task has been created
    initiate_chat_task_created = True

    # Wait for 2 seconds
    await asyncio.sleep(2)

    # Now initiate the chat
    await agent.a_initiate_chat(recipient, message=message)

async def callback(contents: str, user: str, instance: pn.chat.ChatInterface):
    
    global initiate_chat_task_created

    if not initiate_chat_task_created:
        agents = SightseeingPlanAgents()
        groupchat = autogen.GroupChat(agents=[agents.user_proxy(), agents.planner(),agents.critic(),agents.sightseeing_agent(),agents.financial_agent()], messages=[], max_round=20)
        manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=global_vars.llm_config)
        asyncio.create_task(delayed_initiate_chat(agents.user_proxy(), manager, contents))

    else:
        if global_vars.input_future and not global_vars.input_future.done():
            global_vars.input_future.set_result(contents)
        else:
            print("There is currently no input being awaited.")

# 初始化 Panel
pn.extension(design="material")


# 创建文本框和按钮并绑定事件
text_input = pn.widgets.TextAreaInput(width=350)
global_vars.chat_interface = pn.chat.ChatInterface(widgets=[text_input],callback=callback,show_rerun=False, show_undo=False,show_clear=False)
global_vars.chat_interface.send(
    # "南京旅行",
    '''
我需要带领4人的团队前往南京参加学术会议，同时在南京景点参观。
● 地点：东南大学，南京。
● 议程：
6月30日
    ● 确认住宿和交通安排。
    ● 准备会议用品和服装。
7月1日
    ● 上午报到，下午参加开幕式。
    ● 确认第二天的汇报安排。
7月2日
    ● 下午进行汇报。
7月3日-7月4日
    ● 上午参观展板和进行学术交流。
7月5日
    ● 晚上参加闭幕式。
● 成员情况：
  ○ 成员A：李教授：资深学者，注重学术交流和会议活动，对观光兴趣不大，年纪较大，腿脚不便，喜欢高档住宿饮食。
  ○ 成员B：王同学：年轻科研人员，预算有限，喜欢探索新事物新科技，四川人喜欢吃辣。希望既能参加学术活动，又能参观上海的知名景点。
  ○ 成员C：张博士：环保主义者，关注可持续发展，对自然景点和生态园区感兴趣，晕车，酒精过敏，喜欢体验当地特色。
  ○ 成员D：陈教授：喜欢文化艺术，注重文化体验，对紫外线过敏，不喜欢室外活动。
● 住宿情况：集体住宿于南京上秦淮假日酒店。
# ''',
    user="System",
    avatar="🖥️",
)

start_stop_button = pn.widgets.Button(name='开始识别', button_type='primary', width=350)
stt_engine = STTEngine(start_stop_button, text_input)
start_stop_button.on_click(stt_engine.start_stop_recognition)
stt_widgets = pn.Column(global_vars.chat_interface, start_stop_button,name="STT")

chat_interface_card = pn.Card(stt_widgets, title='Chat with agents', styles={'background': 'WhiteSmoke'},width=500, max_height=1000, sizing_mode='stretch_height')

# 创建一个 Markdown 显示区域
global_vars.markdown_display = pn.pane.Markdown("""
# Markdown Sample
This sample text is from [The Markdown Guide](https://www.markdownguide.org)!

## Basic Syntax
These are the elements outlined in John Gruber’s original design document. All Markdown applications support these elements.
""")
# 包裹 Markdown 显示区域的 Card
md_card = pn.Card(global_vars.markdown_display, title='Current Solution', styles={'background': 'WhiteSmoke', 'overflow': 'auto'}, width=500, height=700)
global_vars.chat_status = pn.chat.ChatFeed()
global_vars.chat_status.send(
    "Status panel initialized",
    user="System",
    avatar="🖥️",
)
chat_status_card = pn.Card(global_vars.chat_status, title='Agent status', styles={'background': 'WhiteSmoke', 'overflow': 'auto'},width=500,height=300)
display_layout = pn.Column(md_card,chat_status_card)

# 创建水平布局，并排放置
layout = pn.Row(display_layout,chat_interface_card)

# 将布局标记为可服务对象并设置标题
layout.servable()