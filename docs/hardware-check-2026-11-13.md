# 2026-11-13 実機確認（日本時間）

USB接続した左右ESC・電源Pico・WT61・Xbox 360互換ゲームパッドを使い、実際の `hg-cart drive` で車輪の回転を確認しました。ユーザーからも「一旦動いた」と目視結果を得ています。最後はプログラムを終了し、両ESCのPWM出力OFFとSSR指令OFFを読み取り確認しました。

## 起動できなかった原因と対応

- READMEで指定されていた `config.local.json` が、Git管理外のためこのcheckoutに存在しませんでした。
- 汎用 `config.example.json` のR/Lはnullです。そのまま `check` を実行すると `R/L unset` で停止しました。
- シリアルポートは `root:dialout` の660で、現在のユーザーはdialoutグループに入っていませんでした。ユーザーが一時ACLを設定した後、通信が通りました。
- 過去の機体記録にある左右R/LとUSB固有番号、および今回確認したIMU接続位置を `config.robot.example.json` に収録し、同じ内容の `config.local.json` を作成しました。

機体用設定はジョイスティックモード、速度上限30 RPM、加速10 RPM/s、電源・IMU統合有効です。始動失敗時の自動再試行は無効です。モーター定数の再測定やファームウェア書き込みは行っていません。

## 確認結果

| 項目 | 結果 |
| --- | --- |
| ゲームパッド | `Microsoft X-Box 360 pad` / `045e:028e`、`/dev/input/event14`。通常の入力経路で78フレームを記録 |
| 左ESC | 固有番号末尾3550 → `/dev/ttyACM2`。設定・R/L・校正・PWM停止チェック成功。運転前バス電圧24.555 V |
| 右ESC | 固有番号末尾2326 → `/dev/ttyACM0`。同チェック成功。運転前バス電圧24.731 V |
| 電源Pico | `DE610441238C2E35` → `/dev/ttyACM1`。INA226電圧は約25.4 V、運転前SSR指令ON |
| WT61 | USB接続位置 `pci-0000:00:14.0-usb-0:4.1.4:1.0-port0`。約1秒の静止校正後 `reason=null`。受信・校正確認中のチェックサムエラー0 |
| 実機操作 | 3分間のLIVE運転で十字キー入力を受信。上は目標 `L=+15 / R=-15 RPM`。ユーザーが回転を目視確認 |
| 左輪のESC推定速度 | 始動を含む絶対値最大8.328 RPM。`closed` 状態の記録あり |
| 右輪のESC推定速度 | 始動を含む絶対値最大8.462 RPM。`ramp` / `blend` までを記録 |
| 終了 | `--seconds 180` の時間切れで正常終了。ESC・Pico停止送信エラーなし、ログ欠落0 |
| 終了後の読み取り | 左右とも `state=idle, fault=none, MOE=0, CCER=0x0, est_mrpm=0`。Picoは `relay=0, session=0` |

15 RPMは要求値です。今回の操作は短い入力や方向変更を含み、両輪が同時に連続15 RPMへ到達する確認ではありません。右ESCの `closed` 到達、接地走行、B押下による実機停止試験は今回のログに含まれません。B・Startの操作方法は既存実装に基づいてREADMEへ記載しています。

## 実行コマンドと記録

```bash
uv run hg-cart check --config config.local.json
uv run hg-cart power --config config.local.json --seconds 3
uv run hg-cart imu --config config.local.json --seconds 3
uv run hg-cart drive --config config.local.json --live --seconds 180 --log
```

運転ログは `artifacts/diagnostics/drive-20261113T084648.211061Z.jsonl`（日本時間17:46開始）、終了後の読み取りは `artifacts/hardware/2026-11-13/post-drive-status.json` です。`artifacts/` はGit管理外で、このPC上に保存しています。

再開するときは [READMEの運転手順](https://github.com/taku0625/misachiya_ws/blob/work/src/misachiya_controller/README.md#3-電源を入れて動かす) に従い、物理電源ボタンで駆動電源をONにします。今回の運転前に電源がONだったのは、その時点の実機状態です。今は停止・電源OFFで終了しています。
