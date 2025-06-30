# Dockerfile（ルート直下）
FROM public.ecr.aws/lambda/python:3.12  # ★Lambda 公式ベース

# 依存ライブラリを層にまとめる
COPY requirements.txt .
RUN  pip install -r requirements.txt  -t /var/task

# アプリ本体
COPY . .

# ハンドラを宣言（ファイル名.関数名）
CMD ["main.handler"]
