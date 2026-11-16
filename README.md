# HG-RMA302 ロボットの操作

## まず動かす

**この機体は、初回にR/Lを設定してから、チェック → 走行の順に実行します。** ロボットにつながったLinux PCで、このリポジトリのフォルダーを開いてください。コントローラー・左右ESCのUSBと走行用電源を接続します。

### 1. 初回だけ：モーター定数を保存する

機体別設定の `config.local.json` を使います。ファイルがまだない場合だけ、配布例から作成します。既存のファイルは上書きしません。

```bash
test -e config.local.json || cp -n config.example.json config.local.json
```

`config.local.json` を開き、`left_motor` と `right_motor` の2項目を次の内容に置き換えて保存してください。**他の項目はそのまま残します。** これが `R/L unset` を解消する設定です。

```json
"left_motor": {
  "resistance_ohm": 1.887,
  "inductance_h": 0.000881
},
"right_motor": {
  "resistance_ohm": 1.850,
  "inductance_h": 0.000930
}
```

この値は、左ESC `0670FF343433464757213550`・右ESC `0665FF535157808667132326` につながっていたモーターの測定記録です。**モーターや左右の接続を変更していない機体用です。** 変更した場合は、接続先のモーターに対応する測定値を使います。RはΩ、LはHで、両方 `null` のままではESC側も未設定の場合に起動できません。

配布例から新規作成した場合、電源統合とIMUは無効です。Pico・WT61を使う機体は[初回の準備](#初回の準備)の設定も行ってください。既存の機体別設定がある場合はその設定を維持します。

### 2. チェックして走行を開始する

次のブロックをまとめて実行してください。途中でエラーが出た場合は、その先のコマンドを実行しません。

```bash
uv sync --frozen &&
uv run --frozen hg-cart check --config config.local.json &&
uv run --frozen hg-cart drive --config config.local.json --live --log
```

`check` は回転指令を送らず、左右ESCの設定転送・校正・読み戻しを確認します。PicoやIMUの検査は含みません。R/Lの設定は起動時に自動で転送されるので、毎回編集する必要はありません。

### 3. コントローラーで操作する

両スティックを中央へ戻し、十字キーを離して `READY` を待ちます。IMU有効時は機体を静止させ、校正完了も待ってください。

- **ジョイスティックモード**（配布例）：左スティック縦で前進・後退、右スティック横でその場旋回。タンクモードでは左右スティック縦で各輪を操作します。
- **B**：両輪のPWMを停止し、停止状態を保持します。電源統合が有効ならSSRもOFFにします。
- **Start**：全操作を中立にして押すと、停止保持を解除します。SSRをONにはしません。電源の再投入は物理ボタンで行います。
- **Ctrl-C**：プログラムを終了し、両輪停止を試みます。電源統合が有効ならSSRもOFFにします。

PWM停止は車輪を固定する保持ブレーキではありません。

### 次回からの起動はこの1行

初回の設定とチェックが済んだら、次回からは次のコマンドで起動します。

```bash
uv run --frozen hg-cart drive --config config.local.json --live --log
```

USB機器につながっていないクラウド環境では、実機走行を確認できません。

## ROS 2 Jazzy（work ブランチ）

このチェックアウトは `hg_rma302_driver` という colcon パッケージとしても使えます。
`misachiya_ws/scripts/link_hg_driver.sh` でワークスペースへリンクし、両パッケージを
ビルドすると `ros2 launch misachiya_bringup robot.launch.py` で joy と一緒に起動します。
既定は表示のみで、実走行には `live:=true config_file:=/absolute/path/to/config.local.json`
を指定します。詳しい準備・操作手順は `misachiya_ws/README.md` を参照してください。

ROS 入力は `sensor_msgs/msg/Joy` で、既定は `joy_linux_node` の Linux XInput 配列です。
LB を押して操作し、LB 解放・入力途絶で停止、中立から再開します。B/Start、
電源・IMU 監視、終了時の停止は既存の制御ループを使います。
従来の `uv run hg-cart ...` の入力・操作方法は変わりません。

## コントローラーの操作

起動モードは設定ファイルの `drive.control_mode` で決まります。配布例は `joystick` です。Xbox／Guideボタンがある機種では、押すたびにジョイスティックとタンクを切り替えます。切替後は全操作を中立へ戻してください。Guideボタンのない機種では設定を変更して再起動します。

| 操作 | ジョイスティック | タンク |
| --- | --- | --- |
| 左スティック縦 | 前進・後退 | 左輪の前進・後退 |
| 左スティック横 | 前後進中の曲がり | 使用しない |
| 右スティック横 | その場旋回／走行中の旋回追加 | 使用しない |
| 右スティック縦 | 使用しない | 右輪の前進・後退 |
| 十字キー上下 | 前進・後退 | 前進・後退 |
| 十字キー左右 | その場旋回 | その場旋回 |

従来の `hg-cart drive` ではLBを押す必要はありません。ROSのjoy操作ではLBの保持が必要です。十字キーはスティックより優先し、斜め入力は停止です。十字キーを離すと、その時点のスティック操作へ戻ります。

配布例のスティック上限は30 RPM、十字キー上下は50 RPM、左右は各輪25 RPMです。機体別ファイルの値は異なる場合があります。8 RPM未満の連続駆動には対応しません。

## 初回の準備

必要なものはLinux PC、Python 3.10以上（開発環境の指定は3.12）、`uv`、XInput対応コントローラー、対応ファームウェアの左右ESCです。Pico電源制御とWT61 IMUを使う場合は、それぞれの接続・設定も必要です。

1. コントローラーと左右ESCのUSBを接続します。走行用電源はUSBとは別です。
2. `uv sync --frozen` で依存関係を導入します。
3. `uv run --frozen hg-cart devices` で機器を確認します。
4. 機体別設定がない場合だけ、次のコマンドで新規作成します。既存ファイルは上書きしません。

   ```bash
   test -e config.local.json || cp -n config.example.json config.local.json
   ```

5. `config.local.json` の左右USB固有番号、前進符号、モーター定数、電圧範囲を実機に合わせます。配布例のUSB番号は特定機体の値です。R/Lが両方 `null` の場合はESCに設定済みの値を使い、未設定なら起動できません。
6. Picoを使う機体では `power.enabled=true` と `power.serial` または `power.port` を設定します。WT61を使う機体では `imu.enabled=true` と接続先・取付方向に合う `yaw_sign` を設定します。**配布例では電源統合とIMUの両方が無効です。** [電源・表示の設定](embedded/README.md)も参照してください。
7. 次のチェックが通ったら[起動コマンド](#まず動かす)を実行します。

   ```bash
   uv run --frozen hg-cart check --config config.local.json
   ```

`check` は左右ESCへ停止・設定転送・校正を行い、結果を照合します。回転指令は送りません。PicoやIMUの検査は含みません。Pico有効時はUSB給電だけでもESCのチェックを通せますが、走行開始には駆動電圧が必要です。

## 動かないとき

| 状況 | 確認すること |
| --- | --- |
| `R/L unset` | [冒頭のモーター定数の設定](#1-初回だけモーター定数を保存する)を確認し、機体に合うR/Lを指定する |
| 設定ファイルがない | `config.local.json` を準備する。既存の機体別設定があればそれを使う |
| USB機器が見つからない | `uv run --frozen hg-cart devices` で接続と固有番号を確認する |
| 入力を確認したい | `uv run --frozen hg-cart gamepad --seconds 10`。先に走行プログラムを終了する |
| `USB_ONLY` / `WAIT_POWER` | 走行用電源と物理電源ボタン、左右ESCの電圧を確認する |
| Bのあと動かない | 操作を中立へ戻してStart。SSR再投入は物理ボタン |
| `IMU_CALIBRATING` | 機体を静止させて校正完了を待つ |
| `no valid response to 'cartcap'` | 左右・USB番号・受信バイト数を確認する。走行プログラム終了後に接続と電源を確認し、`check` を再実行する |
| ポート使用中・アクセス権限エラー | 他の走行／入力モニターを終了し、Linuxのデバイスアクセス権を確認する |

`--live` を省いた `drive` は表示専用ですが、実際のゲームパッドが必要です。USB機器なしで確認する場合は次を使います。

```bash
uv run --frozen hg-cart demo --config config.example.json
```

デモは決められた入力例から目標値を計算します。実際のゲームパッド入力や実機の動作確認にはなりません。

## ログと詳しい資料

起動コマンドの `--log` は `artifacts/diagnostics/drive-日時Z.jsonl` に操作・指令・状態を保存します。問題が起きたらCtrl-Cで終了し、表示された保存先のログを確認してください。日時はUTCです。

- [開発環境とテスト](docs/development.md)
- [Pico電源・ESP32表示パネルの配線、設定、ビルド](embedded/README.md)
- [過去の開発・実機検証記録](docs/history.md)：当時の機体固有の情報と検証履歴
