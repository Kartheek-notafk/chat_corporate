FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r frontend/requirements.txt

# Fix for HF Spaces cache permission issue
ENV HF_HOME=/tmp/huggingface

EXPOSE 8501

CMD ["streamlit", "run", "frontend/home.py", "--server.port=7860", "--server.address=0.0.0.0"]
