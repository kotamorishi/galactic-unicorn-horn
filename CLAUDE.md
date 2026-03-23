# Galactic Unicorn Horn

Raspberry Pi等のデバイスから電光掲示板デバイス [Galactic Unicorn Leg](https://github.com/kotamorishi/galactic-unicorn-leg) のAPIを呼び出し、カレンダーの予定を表示するプロジェクト。

## 技術スタック

- **言語:** Python 3
- **主要ライブラリ:** icalendar, requests, python-dotenv
- **対象デバイス:** Raspberry Pi（Galactic Unicorn Leg へHTTPリクエストを送信）
- **カレンダー連携:** iCal URL方式（Google カレンダー・Apple iCal 両対応）

## プロジェクト構成

```
main.py            # メインループ（定期的にカレンダー取得→LED表示）
config.py          # .envからの設定読み込み
.env.example       # 環境変数のテンプレート
requirements.txt   # Pythonパッケージ依存
```

## セットアップ

```bash
pip install -r requirements.txt
cp .env.example .env
# .env にカレンダーURLとデバイスIPを記入
python main.py
```

## 環境変数

`.env` ファイルで管理（`.gitignore` 済み）。`.env.example` を参照。

## Galactic Unicorn Leg API

- `POST /api/message` — テキスト表示（text, display_mode, scroll_speed, color, font等）
- `GET /api/status` — デバイス状態取得
- `POST /api/schedules` — スケジュール設定
- テキスト上限: 128文字
- 同時接続: 1-2本まで、1リクエスト/秒以下を推奨

## 開発ガイドライン

- コードとコメントは日本語OK（変数名・関数名は英語）
- 秘密情報（iCal URL等）は `.env` で管理し、コードに直接書かない
- LEDデバイスへのリクエストは1秒以上の間隔を空ける
- 変更は少量でもこまめにコミットし、リモートへpushすること
