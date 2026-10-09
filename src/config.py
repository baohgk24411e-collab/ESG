import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "lm_studio")
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
LM_STUDIO_MODEL_NAME = os.getenv("LM_STUDIO_MODEL_NAME", "qwen2.5-7b-instruct")

# Per-Agent Model Configuration (Supports multi-model in LM Studio / OpenAI / Gemini)
AGENT1_MODEL_NAME = os.getenv("AGENT1_MODEL_NAME", LM_STUDIO_MODEL_NAME)
AGENT2_MODEL_NAME = os.getenv("AGENT2_MODEL_NAME", LM_STUDIO_MODEL_NAME)
AGENT3_MODEL_NAME = os.getenv("AGENT3_MODEL_NAME", LM_STUDIO_MODEL_NAME)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")

# PhoBERT Settings
PHOBERT_MODEL_NAME = os.getenv("PHOBERT_MODEL_NAME", "vinai/phobert-base-v2")

# Greenwashing Indicators tailored for Vietnam FMCG
INDICATORS = {
    "Selective Disclosure": {
        "name_vn": "Giấu thông tin xấu về môi trường",
        "description": "Nhấn mạnh các hoạt động xanh/bảo vệ môi trường nhỏ lẻ nhưng cố tình giấu hoặc không công bố các thông tin, chỉ số tác động tiêu cực, vi phạm hoặc chất thải gây ô nhiễm môi trường, đặc biệt là sự vắng mặt của các chỉ số môi trường trọng yếu theo ngành chính."
    },
    "Hollow Promise": {
        "name_vn": "Cam kết rỗng (Không có tiến triển/lộ trình)",
        "description": "Đưa ra các cam kết, mục tiêu môi trường rất lớn (như Net Zero, 100% tái chế) nhưng không có lộ trình cụ thể, thiếu mốc thời gian rõ ràng, không có báo cáo tiến độ hoặc số liệu kiểm chứng."
    },
    "Potential Data Mispresentation": {
        "name_vn": "Nguy cơ trình bày sai lệch dữ liệu",
        "description": "Các tuyên bố về môi trường (dưới dạng số liệu hoặc thông tin thực tế) thiếu nhất quán nội bộ, thiếu cơ sở chứng minh đầy đủ hoặc mâu thuẫn với các bằng chứng đáng tin cậy."
    },
    "Misleading Presentation": {
        "name_vn": "Sử dụng ngôn ngữ mập mờ, đánh lừa",
        "description": "Sử dụng các cụm từ gắn nhãn xanh mập mờ như 'thân thiện với môi trường', 'thuần tự nhiên', 'xanh 100%', 'sản phẩm sinh thái' mà không có tiêu chuẩn hoặc chứng nhận môi trường hợp lệ chứng minh."
    }
}

# Maximum debate rounds between Agent 1 and Agent 2
MAX_DEBATE_ROUNDS = 3
