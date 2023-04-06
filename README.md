# バトルスケジュールをDynamoに書き込むLambda関数


## 前提
1. AWSにアカウントがあり、AWS CLIの設定が済んでいること
2. Amazon Prime会員であること
3. Dockerがインストールされていて、Dockerコマンドが使えるようになっていること

## 1.セットアップ
```bash
# 環境変数にAWSの情報を設定する
$ AWS_DEFAULT_REGION=<デフォルトリージョンを指定する>
$ AWS_ACCOUNT_ID=<アカウントIDをしてする>

# ECRにコンテナリポジトリを作成する
aws ecr create-repository \
--repository-name create-ikaring3-data-for-alexa \
--image-scanning-configuration scanOnPush=true \
--region $AWS_DEFAULT_REGION

# ECRにログインする
aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com
```


## 2.開発
### 2.1.環境変数の設定
`.env.sample`の名前を変更し`.env`にしてください  
`.env`を編集して情報を入力する
```bash
# 環境変数
ENVIRONMENT=local
USER_AGENT=<スケジュールAPIに投げる連絡先情報Twitterのアカウントとか>

# AWS
AWS_DEFAULT_REGION=<AWSのデフォルトリージョン>
AWS_ACCESS_KEY_ID=<AWSのACCESS_KEY_ID>
AWS_SECRET_ACCESS_KEY=<AWSのシークレットアクセスキー>
```

### 2.2.コンテナの立ち上げ
```bash
#ローカルのDockerでコンテナ立ち上げ
$ docker compose up -d

#コンテナへのリクエスト
$ curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{}' 

#コンテナの削除
$ docker-compose down --rmi all --volumes --remove-orphans
```


## 3.AWS ECRへのデプロイ
```bash
#コンテナイメージの作成
$ docker build -t create-ikaring3-data-for-alexa .

#コンテナイメージタグの設定
$ docker tag create-ikaring3-data-for-alexa:latest ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/create-ikaring3-data-for-alexa:latest

# ECRへのデプロイ
$ docker push ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/create-ikaring3-data-for-alexa:latest

# コンテナイメージの削除
$ docker rmi ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/create-ikaring3-data-for-alexa
$ docker rmi create-ikaring3-data-for-alexa
```