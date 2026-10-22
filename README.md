# AI実験会社｜会社専用の無料自動化基盤

発信先：[@hatarakujidou.bsky.social](https://bsky.app/profile/hatarakujidou.bsky.social)

**現在：自動投稿は未稼働・初回投稿は未承認。** GitHubは公開リポジトリです。認証情報や個人データをコード、README、Issueなどに書かないでください。個人用Buffer・Grok・Gemini API鍵・他の既存SNS/リポジトリは使用しません。

## 今回配置したもの

- `monitor_bluesky.py`：公開プロフィールの投稿数とフォロワー数を **読み取るのみ**。投稿はしません。
- `.github/workflows/profile_monitor.yml`：15分おきの読み取り専用確認。実行履歴は [Actions](../../actions) で確認。GitHubのスケジュールは遅延・省略の場合があります。
- `publish_bluesky.py`：通常は下書き検証のみ。Bluesky投稿は手動承認と専用Secretがないと実行できません。本文から固定のレコードキーを生成して重複を防ぎます。
- `content/first_post.txt`：**未承認の**最初の投稿下書き。
- `.github/workflows/first_post.yml`：オーナーが手動実行する初回投稿だけ。既定は publish=false で何も公開しません。
- `tests/test_publisher.py`：7件のオフライン安全テスト。インターネットへの投稿は行いません。

## 初回投稿に必要な一度だけの操作

1. Blueskyアプリの **設定 → プライバシーとセキュリティ → アプリパスワード** から会社専用アプリパスワードを作成する。通常のログインパスワードは使用しません。
2. このGitHubリポジトリの **Settings → Secrets and variables → Actions → New repository secret** で、名前を `BSKY_APP_PASSWORD` にして、値として発行したアプリパスワードを入力して保存。**チャットには貼らない**。
3. `content/first_post.txt` の内容を確認して、初回投稿について明示的に承認する。承認までどのボタンでも `publish=true` にしない。
4. 承認後、[Actions](../../actions) → **AI company - first Bluesky post** → **Run workflow** で publish=true を選ぶ。公開成功の報告が出たらBluesky側の投稿URLを開き、本当に見えるか確認する。

認証が未登録のままでも**読み取り専用のプロフィール確認だけ**は動かせます。これらの作業はChatGPT Workを使わずにできます。

## 運用上の制約

- 定期実行は『公開プロフィールの確認』だけであり、AI社員の常時活動やBlueskyの自動投稿が完成したという意味ではありません。
- GitHub Actionsは公開リポジトリの標準GitHub-hosted runnerで追加料金なしで使用できる仕組みがあります。無料条件変更は随時監査し、有料サービスやカード登録を禁止します。
- 公開コードとGitHub Actionsのログは他人も確認できます。秘密情報はGitHub Actions Secrets以外に保存しません。
- 次の開発段階は初回投稿の成功→承認済みキューの安全な自動配信→会社専用の無料外部AIによる調査・検証→報告と改善の自動化です。

公式資料：[Bluesky API](https://bsky.network/docs/bluesky-api/) ／ [GitHub Actionsの仕様](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
