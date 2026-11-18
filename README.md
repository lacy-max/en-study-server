# en-study-server · 儿童英语闯关（后端）

Python FastAPI 单进程，负责两件事：

1. `/tts` —— 文字转语音（edge-tts），返回 mp3 流，带磁盘缓存
2. `/api/chapters` —— 题库读写 + 后台管理页

## 起服务

```bash
cd server      # 本仓库根目录就是原来的 server/
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| GET | `/tts?text=hello&rate=0.9&voice=en-US-AriaNeural` | 返回 `audio/mpeg`，带 md5 磁盘缓存、`Cache-Control: max-age=86400` |
| GET | `/api/chapters?full=1` | 全量题库；`full=0` 只返回目录 |
| GET | `/api/chapters/{id}` | 单个单元 |
| POST | `/api/chapters` | 新建/覆盖单元，需 Header `X-Admin-Token` |
| DELETE | `/api/chapters/{id}` | 删除单元，同上 |
| POST | `/api/chapters/reorder` | 调整单元顺序 |
| GET | `/admin` | 后台管理页 |

## 后台管理

打开 `http://<host>:8000/admin`，输入口令（默认 `xiaoyu`，环境变量 `ADMIN_TOKEN` 可改），口令存在浏览器 localStorage。

单词表每行格式：

```
英文 | 中文 | 挖空答案 | 例句 | 例句中文
```

保存后写回 `data/chapters.json`，前端刷新即生效，不需要重新编译前端。

## 目录

```
app.py             所有接口
admin/index.html   后台管理页（单文件）
data/chapters.json 题库（10 个单元）
Dockerfile         容器化部署
```
