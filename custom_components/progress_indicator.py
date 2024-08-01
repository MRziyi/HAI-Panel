import param
import panel as pn

from panel.viewable import Viewer

pn.extension()  # for notebook

class ProgressIndicator(Viewer):
    current_task = param.Integer(default=1)

    def __init__(self, **params):
        super().__init__(**params)
        self._markdown = pn.pane.Markdown()
        self.tasks=[
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
        ]
        self._sync_markdown()
        self._layout = pn.Column(self._markdown)

    def __panel__(self):
        return self._layout

    @param.depends('current_task', watch=True)
    def _sync_markdown(self):
        content = ""
        for i, task in enumerate(self.tasks):
            if i < self.current_task - 1:
                status = f"### 🟢 {i+1}."
                state = "[Completed]"
            elif i == self.current_task - 1:
                status = f"## 🟡 {i+1}."
                state = "[In Progress]"
            else:
                status = f"### 🔴 {i+1}."
                state = "[To Do]"
            
            content += f"{status} {task['name']} {state}\n"
            content += f"{task['content']}\n\n"

        self._markdown.object = content