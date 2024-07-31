import asyncio
import panel as pn
import autogen
from agents import SightseeingPlanAgents, print_message, print_message_callback
from custom_components.chat_interface import ChatInterface
from custom_components.progress_indicator import ProgressIndicator
import global_vars

async def initiate_chat(contents):

    agents = SightseeingPlanAgents()
    global_vars.groupchat = autogen.GroupChat(agents=[agents.user_proxy(), agents.process_manager(),agents.critic(),agents.sightseeing_agent(),agents.financial_agent()], admin_name="Admin",messages=[], max_round=20)
    global_vars.groupchat_manager = autogen.GroupChatManager(groupchat=global_vars.groupchat, llm_config=global_vars.llm_config)
    await agents.user_proxy().a_initiate_chat(global_vars.groupchat_manager, message=contents)

def init():
    # 初始化 Panel
    pn.extension(design="material")

    global_vars.chat_interface=ChatInterface()
    # 创建一个 Markdown 显示区域
    global_vars.markdown_display = pn.pane.Markdown("""# 时间安排

| 日期\时间 | 上午           | 下午         | 晚上                   |
| --------- | -------------- | ------------ | :--------------------- |
| 6月30日   | x              | 航班前往南京 | 入住南京上秦淮假日酒店 |
| 7月1日    | 会议报道       | 会议开幕式   | -                      |
| 7月2日    | -              | 论文汇报     | -                      |
| 7月3日    | [可选]参观展板 | -            | -                      |
| 7月4日    | [可选]学术交流 | -            | -                      |
| 7月5日    | -              | -            | 闭幕式                 |

# 预算安排

| 日期\项目 | 门票 | 餐饮 | 交通 | 总计 |
| --------- | ---- | ---- | :--- | ---- |
| 7月1日    | -    | -    | -    |      |
| 7月2日    | -    | -    | -    |      |
| 7月3日    | -    | -    | -    |      |
| 7月4日    | -    | -    | -    |      |
| 7月5日    | -    | -    | -    |      |
| 总计      |      |      |      |      |
""")
    # 包裹 Markdown 显示区域的 Card
    md_card = pn.Card(global_vars.markdown_display, title='Current Solution', styles={'background': 'WhiteSmoke', 'overflow': 'auto'}, width=500, height=700)

    global_vars.progress_indicator = ProgressIndicator()
    chat_status_card = pn.Card(global_vars.progress_indicator, title='Progress Indicator', styles={'background': 'WhiteSmoke', 'overflow': 'auto'},width=500,height=250)
    display_layout = pn.Column(md_card,chat_status_card)

    # 创建水平布局，并排放置
    layout = pn.Row(display_layout,global_vars.chat_interface)

    # 将布局标记为可服务对象并设置标题
    layout.servable()



# Initialize Panel in the main thread
init()
# Run the chat function as a task
global_vars.chat_task = asyncio.create_task(initiate_chat(
    # "南京旅行",
    '''我需要带领4人的团队前往南京参加学术会议，同时在南京景点参观。
* 地点：东南大学，南京。
* 议程：
    * 6月30日
        * 确认住宿和交通安排。
        * 准备会议用品和服装。
    * 7月1日
        * 上午报到，下午参加开幕式。
        * 确认第二天的汇报安排。
    * 7月2日
        * 下午进行汇报。
    * 7月3日-7月4日
        * 上午可选参观展板或进行学术交流。
    * 7月5日
        * 晚上参加闭幕式。
* 成员情况：
    * 成员A：李教授：资深学者，注重学术交流和会议活动，对观光兴趣不大，年纪较大，腿脚不便，喜欢高档住宿饮食。
    * 成员B：王同学：年轻科研人员，预算有限，喜欢探索新事物新科技，四川人喜欢吃辣。希望既能参加学术活动，又能参观上海的知名景点。
    * 成员C：张博士：环保主义者，关注可持续发展，对自然景点和生态园区感兴趣，晕车，酒精过敏，喜欢体验当地特色。
    * 成员D：陈教授：喜欢文化艺术，注重文化体验，对紫外线过敏，不喜欢室外活动。
* 住宿情况：集体住宿于南京上秦淮假日酒店。''',
))