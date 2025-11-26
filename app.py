from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    # 本地运行时使用 8000 端口
    app.run(host='0.0.0.0', port=8000)
