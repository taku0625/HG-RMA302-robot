# HG-RMA302 ファームウェア・検証記録

車体の Python 制御コード、ROS 2 ノード、joy 操作、機体用 JSON の配布例と Python テストは
[misachiya_ws/src/misachiya_controller](https://github.com/taku0625/misachiya_ws/tree/work/src/misachiya_controller)
へ移しました。制御コードの実装は移行先だけで管理します。

## 車体を操作する

ROS 2 Jazzy のビルド・joy 操作は
[misachiya_ws の手順](https://github.com/taku0625/misachiya_ws/blob/work/README.md)を参照してください。
`misachiya_ws` だけで車体制御をビルドできます。旧 `hg_rma302_driver` リンクは不要です。

従来の `uv run hg-cart ...` も、移行先の `src/misachiya_controller` で使えます。

```bash
cd /path/to/misachiya_ws/src/misachiya_controller
uv sync --frozen
uv run --frozen hg-cart check --config /absolute/path/to/config.local.json
# 実際に走行する場合のみ
uv run --frozen hg-cart drive --config /absolute/path/to/config.local.json --live --log
```

機体用 `config.local.json`、診断ログ、既存のローカル成果物は移動・上書きしません。
移行先でも既存 JSON の絶対パスを指定できます。モーター R/L の設定や単独操作の詳細は
[controller の説明](https://github.com/taku0625/misachiya_ws/blob/work/src/misachiya_controller/README.md)にあります。
Python の import 名は `hg_rma302` から `misachiya_controller` に変わりました。

## このリポジトリに残すもの

- `embedded/`: Pico 電源コントローラと ESP32 表示パネル、および SDK 模擬テスト。
- `firmware/`: 別管理の STM32 ESC プロジェクトへ適用するパッチと制御ヘッダー。
- `tests/*.cpp`: ESC のネイティブ制御試験。
- `tools/build_embedded.py`: Pico/ESP32 のビルドと成果物作成。
- `docs/history.md`: 過去の開発・実機検証記録。

[ファームウェアの開発・テスト](docs/development.md)、
[電源・表示の配線・ビルド](embedded/README.md)、[実機確認記録](docs/hardware-check-2026-11-13.md)、[詳細仕様](docs/technical-reference.md)、[過去の記録](docs/history.md)を参照してください。
