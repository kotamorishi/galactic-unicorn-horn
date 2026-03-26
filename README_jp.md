# Galactic Unicorn Horn

Raspberry Pi等のデバイスから電光掲示板デバイス [Galactic Unicorn Leg](https://github.com/kotamorishi/galactic-unicorn-leg) のAPIを呼び出し、カレンダーの予定をLEDディスプレイにスクロール表示するプロジェクトです。

## 対応カレンダー

- **Apple カレンダー（iCloud）** — CalDAV認証方式。カレンダーを公開設定にする必要なし
- **Google カレンダー** — iCal URL方式。秘密のアドレスを使用

両方を同時に使用することもできます。

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. フォントの配置

`fonts/` ディレクトリに [PixelMplus](https://github.com/itouhiro/PixelMplus) をダウンロードして配置してください。

```
fonts/
  PixelMplus10-Regular.ttf
  PixelMplus12-Regular.ttf (任意)
  PixelMplus12-Bold.ttf    (任意)
```

> PixelMplusはフリーフォントです。ライセンスの都合上リポジトリには含めていません。

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集して、デバイスIPとカレンダーの設定を行います。

### 4. 実行

```bash
python main.py
```

## カレンダーの設定方法

### Apple カレンダー（iCloud）

Apple カレンダーはCalDAV認証方式で接続します。カレンダーを「公開」にする必要はありません。

#### 手順

1. [appleid.apple.com](https://appleid.apple.com/) にログイン
2. **サインインとセキュリティ** → **アプリ用パスワード** を選択
3. **「+」** ボタンでパスワードを生成（名前は自由。例：「LED掲示板」）
4. 表示される `xxxx-xxxx-xxxx-xxxx` 形式のパスワードをコピー
5. `.env` に以下を設定:

```
ICLOUD_USERNAME=your@icloud.com
ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

これだけでiCloud上の全カレンダーからイベントが取得されます。

> `ICAL_URLS` の設定は不要です。

### Google カレンダー

Google カレンダーはiCal URL方式で接続します。

#### 手順

1. [Google カレンダー](https://calendar.google.com/) を開く
2. 左サイドバーの対象カレンダーの **「⋮」** → **「設定と共有」**
3. **「iCal形式の秘密のアドレス」** のURLをコピー
4. `.env` に以下を設定:

```
ICAL_URLS=https://calendar.google.com/calendar/ical/xxxxxxxx/basic.ics
```

複数のカレンダーを使う場合はカンマ区切りで指定できます:

```
ICAL_URLS=https://calendar.google.com/.../1.ics,https://calendar.google.com/.../2.ics
```

> このURLは推測不可能なランダム文字列を含んでおり、URLを知っている人だけがアクセスできます。カレンダーを「公開」にする必要はありません。

### Apple + Google の併用

両方を設定すれば、全てのイベントが時刻順に統合されて表示されます。

```
ICLOUD_USERNAME=your@icloud.com
ICLOUD_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
ICAL_URLS=https://calendar.google.com/calendar/ical/xxxxxxxx/basic.ics
```

## 表示タイミングの仕組み

イベントの開始時刻に基づいて表示されます。例えば `09:00-10:00 ABC` というイベントの場合：

| 時刻 | 動作 | 色 |
|------|------|-----|
| 08:49 | 表示OFF | — |
| 08:50 | 通知音が鳴り、`09:00-10:00 ABC` を表示 | 緑 |
| 09:00 | 色が赤に変わる（イベント開始） | 赤 |
| 09:05 | 表示クリア | — |

- **開始10分前**: 表示ON（緑バー + 白テキスト）+ 通知音
- **開始5分前**: 2回目の通知音
- **開始時刻**: バーの色が赤に変更
- **開始5分後**: 表示クリア
- 進行中のイベント（赤）は、次のイベント（緑）より優先表示されます
- ディスプレイ上部に1pxのカラーインジケーターバーが表示されます

## LLM連携（LLMHAT / Ollama）

Raspberry Pi上で [Ollama](https://ollama.com/) が動作している場合（例：[Raspberry Pi AI HAT+ 2](https://www.raspberrypi.com/products/ai-hat-plus/) 使用時）、ローカルLLMを使ってイベントのテキストを自然な日本語に自動変換します。

**変換例：**
- 変換前: `09:00-10:00 打ち合わせ`
- 変換後: `9時から打ち合わせです`

LLMは起動時に自動検出されます。Ollamaが利用できない場合は従来通りのフォーマットで表示されます。LLMの結果はイベントごとにキャッシュされ、同じイベントに対する繰り返しの推論を避けます。

OllamaのURLやモデルを指定する場合は、`.env` に `OLLAMA_URL` と `OLLAMA_MODEL` を設定してください。

## 設定一覧

| 環境変数 | 説明 | デフォルト |
|---------|------|-----------|
| `DEVICE_IPS` | デバイスIPアドレス（カンマ区切りで複数可） | ー |
| `DEVICE_IP` | 単一デバイスIP（`DEVICE_IPS` 未設定時のフォールバック） | `192.168.1.100` |
| `ICLOUD_USERNAME` | Apple ID（メールアドレス） | ー |
| `ICLOUD_APP_PASSWORD` | iCloudアプリ用パスワード | ー |
| `ICAL_URLS` | iCal URL（カンマ区切りで複数可） | ー |
| `FETCH_INTERVAL` | カレンダー取得間隔（秒） | `300` |
| `SCROLL_SPEED` | スクロール速度（`slow` / `medium` / `fast`） | `medium` |
| `FONT_PATH` | フォントファイルのパス | `fonts/PixelMplus10-Regular.ttf` |
| `FONT_SIZE` | フォントサイズ（px） | `10` |
| `OLLAMA_URL` | Ollama APIのURL（LLM整形用） | 自動検出 `localhost:11434` |
| `OLLAMA_MODEL` | 使用するOllamaモデル名 | 自動選択（最初のモデル） |

## サービスとして実行（Raspberry Pi）

バックグラウンドサービスとして登録すると、起動時に自動実行されます：

```bash
# サービスファイルをコピー
sudo cp galactic-unicorn-horn.service /etc/systemd/system/

# インストール先やユーザーが /home/pi/ と異なる場合は編集
sudo nano /etc/systemd/system/galactic-unicorn-horn.service

# 有効化して起動
sudo systemctl daemon-reload
sudo systemctl enable galactic-unicorn-horn
sudo systemctl start galactic-unicorn-horn
```

よく使うコマンド：

```bash
# ステータス確認
sudo systemctl status galactic-unicorn-horn

# ログを表示
journalctl -u galactic-unicorn-horn -f

# 設定変更後に再起動
sudo systemctl restart galactic-unicorn-horn

# 停止
sudo systemctl stop galactic-unicorn-horn
```

主な特徴：
- 起動時に**自動スタート**（`enable`）
- クラッシュ時に**自動再起動**（10秒後にリスタート）
- **ログ**はjournaldで管理（ログファイルのローテーション不要）
- **ネットワーク接続後**に起動

## セキュリティについて

- `.env` ファイルは `.gitignore` に含まれており、Gitにコミットされません
- iCloudアプリ用パスワードが漏洩した場合は [appleid.apple.com](https://appleid.apple.com/) から無効化できます
- Google カレンダーの秘密のアドレスが漏洩した場合はGoogle カレンダーの設定からリセットできます

## テスト

```bash
python3 -m pytest tests/ -v
```
