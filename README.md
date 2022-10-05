# room-monitor
BME680とArduino Yun Miniを使った部屋の環境モニタリングをするためのコード
https://qiita.com/k-akie/items/9a3528c5345db045e061

## フォルダ構成
- arduino
  - Arduino Yun Mini用のコード
- functions
  - Google Cloud Functions用のコード
    - register_monitoring_data: モニタリングデータ登録
    - slack_app: Slackアプリ(最新のモニタリングデータ参照コマンド)

## システム構成
![system-configuration](./system-configuration.png)
