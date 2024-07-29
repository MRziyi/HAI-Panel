import param
import panel as pn

from panel.viewable import Viewer

pn.extension()  # for notebook

class ProgressIndicator(Viewer):
    tasks = param.List(doc="A list of tasks.", default=[
        {"name": "Title for task1", "content": "content for task1"},
        {"name": "Title for task2", "content": "content for task2"},
        {"name": "Title for task3", "content": "content for task3"}
    ])
    
    current_task = param.Integer(default=1)

    def __init__(self, **params):
        super().__init__(**params)
        self._markdown = pn.pane.Markdown()
        self._sync_markdown()
        self._layout = pn.Column(self._markdown)

    def __panel__(self):
        return self._layout

    @param.depends('tasks', 'current_task', watch=True)
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