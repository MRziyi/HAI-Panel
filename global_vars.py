from dotenv import load_dotenv
import os

load_dotenv()  # 加载 .env 文件中的所有环境变量

chat_interface = None
chat_status = None
markdown_display = None
progress_indicator = None

input_future=None
chat_task=None
groupchat=None
groupchat_manager=None
is_interrupted=None


llm_config={"config_list": [
            {
                'model': 'gpt-4o',
                "api_key": os.environ["OPENAI_API_KEY"]
            }
            ], 
            "temperature":0, 
            "timeout":3000,
            "seed": 53}