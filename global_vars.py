from dotenv import load_dotenv
import os
import panel as pn
import autogen

load_dotenv()  # 加载 .env 文件中的所有环境变量

app = None
app_layout= pn.Column("Modal")
modal_content = pn.Column("Modal")

chat_interface = None
chat_status = None
markdown_display = None
progress_indicator = None

input_future=None
chat_task=None
groupchat=None
groupchat_manager=None


llm_config={"config_list": [
            {
                'model': 'gpt-4o-2024-08-06',
                "api_key": os.environ["OPENAI_API_KEY"],
                # "base_url":"https://azureport.eastus.cloudapp.azure.com "
            }
            ], 
            "temperature":0, 
            "timeout":3000,
            "seed": 53}

global_assistant= autogen.AssistantAgent(
            name='Assistant',
            llm_config=llm_config,
            human_input_mode="NEVER",
            system_message='你是Assistant，需要根据用户的要求，参考给出的例子给出json格式的输出',
        )
smaller_model_config={"config_list": [
            {
                'model': 'gpt-4o-mini',
                "api_key": os.environ["OPENAI_API_KEY"],
                # "base_url":"https://azureport.eastus.cloudapp.azure.com "
            }
            ], 
            "temperature":0, 
            "timeout":3000,
            "seed": 53}

global_formatter= autogen.AssistantAgent(
            name='Formatter',
            llm_config=smaller_model_config,
            human_input_mode="NEVER",
            system_message='''你是Formatter，需要将输入的内容，按照用户要求给出json格式的输出''',
        )

speaker_selector= autogen.AssistantAgent(
            name='SpeakerSelector',
            llm_config=smaller_model_config,
            human_input_mode="NEVER",
            system_message='''You are in a role play game. The roles in <roles_info> are available. Read the message in <message>. Then select the next role from <role_list> to play. Only return the role name (pure string).''',
        )

