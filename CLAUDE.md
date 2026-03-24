# Galactic Unicorn Horn

Raspberry Pi等のデバイスから電光掲示板デバイス [Galactic Unicorn Leg](https://github.com/kotamorishi/galactic-unicorn-leg) のAPIを呼び出し、カレンダーの予定を表示するプロジェクト。

## 技術スタック

- **言語:** Python 3
- **主要ライブラリ:** icalendar, requests, python-dotenv, Pillow
- **対象デバイス:** Raspberry Pi（Galactic Unicorn Leg へHTTPリクエストを送信）
- **カレンダー連携:** iCal URL方式（Google カレンダー・Apple iCal 両対応）

## プロジェクト構成

```
main.py            # メインループ（定期的にカレンダー取得→LED表示）
config.py          # .envからの設定読み込み
renderer.py        # テキスト→ビットマップ変換（Pillow）
.env.example       # 環境変数のテンプレート
requirements.txt   # Pythonパッケージ依存
tests/             # pytest テスト
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

- `POST /api/bitmap` — ビットマップ表示（本プロジェクトで使用。monoフォーマット、base64エンコード、最大幅5000px）
- `DELETE /api/bitmap` — ビットマップクリア（テキストモードに戻る）
- `POST /api/message` — テキスト表示（英数字・記号のみ対応。日本語不可）
- `GET /api/status` — デバイス状態取得
- `POST /api/schedules` — スケジュール設定
- 同時接続: 1-2本まで、1リクエスト/秒以下を推奨

**重要:** テキストAPI (`POST /api/message`) は英数字・記号のみ対応。日本語表示にはビットマップAPI (`POST /api/bitmap`) を使うこと。本プロジェクトではカレンダーの予定に日本語が含まれるため、常にビットマップAPIを使用する。

## テスト

```bash
python3 -m pytest tests/ -v
```

## 開発ガイドライン

- コードとコメントは日本語OK（変数名・関数名は英語）
- 秘密情報（iCal URL等）は `.env` で管理し、コードに直接書かない
- LEDデバイスへのリクエストは1秒以上の間隔を空ける
- 変更は少量でもこまめにコミットし、リモートへpushすること
