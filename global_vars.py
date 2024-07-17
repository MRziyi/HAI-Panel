
chat_interface = None
chat_status = None
markdown_display = None

input_future=None

avatars = {
    "FinancialAgent": "💵",
    "SightseeingAgent":"🏜️",
    "Admin":"👨🏻‍💼",
    'Planner':"🗓",
    'Critic':'📝'
}

llm_config={"config_list": [
            {
                'model': 'gpt-4o',
            }
            ], 
            "temperature":0, 
            "timeout":3000,
            "seed": 53}