[README.md](https://github.com/user-attachments/files/26508379/README.md)
# NeuroSciHub

脳神経外科・BMI/BCI・人型ロボット開発・医療AIの最新医学文献を  
**毎週土曜日 09:00 JST に自動収集・掲載**する個人学習サイト。

🌐 **公開URL**: `https://あなたのID.github.io/neuroscihub/`

---

## 📁 プロジェクト構成

```
neuroscihub/
├── index.html                     ← サイト本体（単一ファイル）
├── 404.html                       ← GitHub Pages SPA用リダイレクト
├── robots.txt                     ← SEO用クローラー設定
├── data/
│   └── papers.json                ← 週次収集データ（GitHub Actions が自動更新）
├── scripts/
│   └── fetch_papers.py            ← 論文収集スクリプト（Python）
└── .github/
    └── workflows/
        └── weekly_fetch.yml       ← GitHub Actions 自動実行定義
```

---

## 🚀 Step 1: GitHubリポジトリの作成・公開

### 1-1. リポジトリ作成

1. https://github.com にサインイン
2. 右上「＋」→「New repository」
3. Repository name: **`neuroscihub`**（または任意の名前）
4. **Public** を選択（GitHub Pages 無料利用の条件）
5. README・.gitignore は追加しない（後でこのREADMEをアップロード）
6. 「Create repository」をクリック

### 1-2. ファイルをアップロード

#### 方法A：GitHub Web UI（コマンド不要）

1. 作成したリポジトリのページで「uploading an existing file」をクリック
2. 以下のファイルをドラッグ&ドロップ：
   - `index.html`
   - `404.html`
   - `robots.txt`
   - `README.md`
3. フォルダは「Create new file」で作成：
   - `data/papers.json` → ファイル内容を貼り付け
   - `scripts/fetch_papers.py` → ファイル内容を貼り付け
   - `.github/workflows/weekly_fetch.yml` → ファイル内容を貼り付け
4. 「Commit changes」

#### 方法B：Git コマンド（ターミナル）

```bash
# リポジトリをクローン
git clone https://github.com/あなたのID/neuroscihub.git
cd neuroscihub

# このプロジェクトのファイルをすべてコピーしてから：
git add .
git commit -m "🚀 初回公開"
git push origin main
```

### 1-3. GitHub Pages を有効化

1. リポジトリの「**Settings**」タブ
2. 左メニュー「**Pages**」
3. Source: **Deploy from a branch**
4. Branch: **main** / **/ (root)**
5. 「**Save**」
6. 数分後に `https://あなたのID.github.io/neuroscihub/` で公開 ✅

---

## 🔑 Step 2: APIキーの取得と設定

### PubMed APIキー（無料・推奨）

1. https://www.ncbi.nlm.nih.gov/account/ でアカウント作成
2. 右上のユーザー名 → **Account Settings**
3. **API Key Management** → **Create an API Key**
4. 生成されたキー（英数字32文字）をコピー

**効果**: なし→3req/秒、あり→10req/秒（収集速度が大幅向上）

### Semantic Scholar APIキー（無料・任意）

1. https://www.semanticscholar.org/product/api にアクセス
2. 「**Get API Key**」→ メールアドレスで登録
3. 送られてきたキーをコピー

### GitHub Secrets に登録

1. リポジトリの「**Settings**」→「**Secrets and variables**」→「**Actions**」
2. 「**New repository secret**」で以下を順番に追加：

| Name | Value | 説明 |
|---|---|---|
| `PUBMED_API_KEY` | NCBIで取得した32文字のキー | 論文検索の速度向上 |
| `S2_API_KEY` | Semantic Scholarのキー | 注目度スコア取得 |
| `CONTACT_EMAIL` | あなたのメールアドレス | CrossRef API礼儀的利用 |

---

## ⚙️ Step 3: 初回自動収集を手動実行

1. リポジトリの「**Actions**」タブ
2. 左メニュー「**週次論文自動収集・デプロイ**」
3. 「**Run workflow**」ボタン → 「**Run workflow**」
4. 実行完了（約5〜15分）後、`data/papers.json` が更新される
5. サイトをリロードして論文が表示されることを確認 ✅

### 自動実行スケジュール
```
毎週土曜日 09:00 JST（= UTC 00:00）
GitHub Actions cron: "0 0 * * 6"
```

---

## 💰 Step 4: 収益化設定

### Google AdSense

1. https://adsense.google.com で申請
2. サイトURL: `https://あなたのID.github.io/neuroscihub/`
3. 審査通過後（通常1〜2週間）、管理画面でコードを取得
4. `index.html` の `<head>` タグ内に追加：

```html
<!-- Google AdSense -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
```

5. 広告を表示したい箇所（AdBannerの `<div>` 内）にユニット広告コードを追加

**AdSense審査通過のポイント**:
- プライバシーポリシーページが存在する ✅（実装済み）
- 運営者情報が開示されている ✅（実装済み）
- コンテンツが十分な量・質である（論文が20件以上蓄積されてから申請推奨）
- サイトがHTTPS（GitHub Pagesは自動対応）✅

### Amazonアソシエイト

1. https://affiliate.amazon.co.jp で申請
2. 審査通過後、商品リンクを論文詳細カードに追加可能
3. 例：「この論文の参考になる書籍 →」として関連医学書を紹介

### ステルスマーケティング規制対応（2023年10月〜義務）

アフィリエイトリンクを掲載する全ページに以下を明記（フッターに実装済み）：
> 本サイトにはアフィリエイトリンク・広告が含まれます

---

## 🌐 Step 5: 独自ドメイン設定（任意・推奨）

### ドメイン取得

- [お名前.com](https://www.onamae.com/)：年間1,000〜2,000円
- [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/)：定価提供（最安値水準）
- 例: `neuroscihub.jp` / `neuromed-hub.net`

### DNS設定（Cloudflare推奨）

```
# CNAMEレコードを追加
Type: CNAME
Name: www（またはルートドメイン）
Target: あなたのID.github.io
```

### GitHub Pages にドメイン登録

1. リポジトリ Settings → Pages
2. Custom domain: `www.あなたのドメイン.jp`
3. 「Save」→「Enforce HTTPS」にチェック ✅

### robots.txt のドメインを更新

```
Sitemap: https://www.あなたのドメイン.jp/sitemap.xml
```

---

## 📊 Google Analytics 設定（任意）

1. https://analytics.google.com でプロパティ作成
2. 測定ID（G-XXXXXXXXXX）を取得
3. `index.html` の `<head>` 内に追加：

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

---

## 🔧 コンテンツのカスタマイズ

### 検索クエリの調整

`scripts/fetch_papers.py` の `SEARCH_QUERIES` 辞書を編集することで  
各分野・小分類の検索条件をカスタマイズできます。

```python
# 例: 脳卒中外科の検索クエリを調整
"stroke": (
    '("stroke"[MeSH] OR ...) AND ...'
),
```

PubMed検索構文: https://pubmed.ncbi.nlm.nih.gov/help/

### BMI/BCI 詳細記事の追加

`index.html` の `const bmiDetails = [...]` 配列に追記：

```javascript
{
  id: 'bd_new',
  category: 'company_news',  // company_news/conference/clinical_application/brain_analysis/ai_technology/japan_research/unknown_frontiers
  company: '企業名',
  emoji: '🔵',
  title: '記事タイトル',
  summary: '概要（カード表示用・2-3文）',
  tags: ['タグ1', 'タグ2'],
  content: `## セクション1\n内容...\n## セクション2\n内容...`,
  source_url: 'https://...',
},
```

### popular/new 判定閾値の調整

```python
POPULAR_MIN_CITATIONS = 10   # この被引用数以上 → popular列
POPULAR_MIN_ALTMETRIC = 30   # このAltmetricスコア以上 → popular列 & 🔥HOT
```

---

## 🧪 ローカルで動作確認

```bash
# Python の簡易サーバー起動
cd neuroscihub
python -m http.server 8080
# → http://localhost:8080 で確認

# 論文収集スクリプトをローカルで実行（APIキーが必要）
pip install requests
PUBMED_API_KEY=your_key python scripts/fetch_papers.py
```

---

## ❓ トラブルシューティング

| 問題 | 対処 |
|---|---|
| サイトが表示されない | Settings → Pages が有効か確認。デプロイに5分程度かかる場合あり |
| 論文が取得されない | Actions タブでエラーログを確認。APIキーの設定を再確認 |
| PubMedのRate limit | `PUBMED_API_KEY` を設定する（10req/秒に緩和） |
| 0件しか取得できない | クエリの日付範囲を確認。`DAYS_BACK` を14に増やしてみる |
| AdSense審査落ち | コンテンツ量・品質を増やしてから再申請。プライバシーポリシー確認 |

---

## 📝 ライセンス・免責

- サイトコード：MIT License
- 掲載論文情報：各出版社・著者の著作権に帰属
- 本サイトの情報は学習目的で収集したものです。臨床判断の根拠として使用しないでください。
