# Kintone-Notion Sync App

Kintoneの2つのアプリ（App 52とApp 31）からデータを取得し、Notionのデータベースに同期するWebアプリケーションです。

## 🔒 セキュリティ改善点

このアプリケーションは以下のセキュリティ対策を実装しています：

1. **環境変数によるシークレット管理**: すべてのAPIキー・トークンは環境変数として管理され、コードには含まれていません
2. **`.gitignore`設定**: `.env`ファイルはGit管理から除外され、誤ってコミットされることを防ぎます
3. **Vercel環境変数**: 本番環境ではVercelのEnvironment Variablesに安全に保存されます

## 📱 機能

- モバイルフレンドリーなUIデザイン
- 日付ベースでの同期フィルタリング
- リアルタイムの同期ステータス表示
- エラーログの詳細表示

## 🚀 Vercelへのデプロイ手順

### 1. Vercelプロジェクトの作成

1. [Vercel](https://vercel.com)にログイン
2. 「New Project」をクリック
3. このフォルダをGitHubにプッシュしている場合は、リポジトリを選択
4. またはVercel CLIを使用してデプロイ（下記参照）

### 2. 環境変数の設定

Vercelのプロジェクト設定で以下の環境変数を設定してください：

```
NOTION_TOKEN=your_notion_integration_token
KINTONE_TOKEN_APP_52=your_kintone_app52_token
KINTONE_TOKEN_APP_31=your_kintone_app31_token
```

> [!IMPORTANT]
> セキュリティ上、これらのトークンは絶対にGitにコミットしないでください。

### 3. デプロイ

#### 方法A: Vercel CLI（推奨）

```bash
# Vercel CLIをインストール（初回のみ）
npm install -g vercel

# プロジェクトフォルダでデプロイ
cd kintone_notion_app
vercel

# 本番環境へデプロイ
vercel --prod
```

#### 方法B: GitHub連携

1. GitHubにリポジトリを作成
2. コードをプッシュ（`.env`は除外される）
3. VercelでGitHubリポジトリをインポート
4. 環境変数を設定
5. デプロイ

### 4. タイムアウト設定（必要に応じて）

大量のレコードを処理する場合、Vercelのサーバーレス関数のタイムアウト設定を調整してください：

- Hobby Plan: 最大10秒
- Pro Plan: 最大60秒まで設定可能

`vercel.json`に以下を追加：

```json
{
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": { "maxDuration": 60 }
    }
  ]
}
```

## 🧪 ローカルでのテスト

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env`ファイルを作成し、以下の内容を設定：

```
NOTION_TOKEN=your_notion_integration_token
KINTONE_TOKEN_APP_52=your_kintone_app52_token
KINTONE_TOKEN_APP_31=your_kintone_app31_token
```

### 3. アプリケーションの起動

```bash
python api/index.py
```

### 4. ブラウザでアクセス

```
http://localhost:5000
```

## 📁 プロジェクト構造

```
kintone_notion_app/
├── api/
│   └── index.py              # Flaskアプリケーション（エントリーポイント）
├── templates/
│   └── index.html            # モバイル対応UIテンプレート
├── sync_kintone_notion.py    # 同期ロジック（リファクタリング済み）
├── requirements.txt          # Python依存関係
├── vercel.json              # Vercel設定
├── .env                     # ローカル環境変数（Gitignored）
└── .gitignore               # Git除外設定
```

## 🔧 技術スタック

- **Backend**: Flask (Python)
- **API**: Kintone REST API, Notion API
- **Deployment**: Vercel Serverless Functions
- **Frontend**: Vanilla HTML/CSS/JavaScript

## ⚠️ 注意事項

1. **APIレート制限**: Notion/Kintone APIのレート制限に注意してください。大量のレコード処理時は時間がかかる場合があります。
2. **タイムアウト**: Vercelの無料プランでは10秒のタイムアウトがあります。大量データの場合はProプランの検討をお勧めします。
3. **エラーハンドリング**: 現在の実装では基本的なエラーログを提供していますが、本番運用では詳細なログ記録が推奨されます。

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. すべての環境変数が正しく設定されているか
2. Notion Integrationがデータベースにアクセスできるか
3. Kintone APIトークンが有効で、適切な権限があるか
