import panel as pn
import global_vars
from pages.welcome_page.welcome_page import WelcomePage
pn.extension()

# 创建 Panel 服务器
global_vars.app = pn.template.VanillaTemplate(title='POLARIS')
global_vars.app.main.append(global_vars.app_layout)
global_vars.app.modal.append(global_vars.modal_content)

# 运行 Panel 服务器
global_vars.app.servable()

WelcomePage()