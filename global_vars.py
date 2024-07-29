
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
            }
            ], 
            "temperature":0, 
            "timeout":3000,
            "seed": 53}