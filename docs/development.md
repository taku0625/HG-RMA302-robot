# ファームウェアの開発とテスト

Python の車体制御、ROS ノード、Python テスト、`uv.lock` は
[misachiya_controller](https://github.com/taku0625/misachiya_ws/tree/work/src/misachiya_controller)
へ移しました。単独実行・機体用 JSON・Python の準備は移行先の README にあります。
このリポジトリではファームウェアとその検証記録を管理します。

クラウドの既存チェックアウトを使います。作業ごとに Git worktree を作る必要はありません。
以下は HG リポジトリのルートで実行します。Python 側の追加ライブラリは不要です。

## 実機なしで検証する

```bash
python3 -m unittest discover -s embedded/tests -v
mkdir -p artifacts/validation/native
for name in current_sum_guard startup_lock; do
  g++ -std=c++17 -O2 -Wall -Wextra -Werror -Ifirmware \
    "tests/${name}_test.cpp" -o "artifacts/validation/native/${name}_test" || exit
  "artifacts/validation/native/${name}_test" || exit
done
```

組み込みのテストは SDK を模擬して C コードをコンパイルし、電源制御のメインループなどを実行します。
`python3`、`cc`、`g++` が必要です。上記の C++ 2 本は外部 ESC ソースなしで実行できます。

残りの C++ 試験10本には、別の STM32 ESC プロジェクトの `motor_control.hpp`、
`motor_speed.hpp`、`motor_board_config.hpp` 等が必要です。このリポジトリだけでは実行できません。
`firmware/*.patch` は外部プロジェクト向けの差分で、完全な ESC ソースではありません。

## ファームウェアをビルドする場合

[Pico/ESP32 の手順](../embedded/README.md#ビルド)を参照してください。
Pico SDK、ARM toolchain、CMake、picotool が必要です。
ESP32 もビルドする場合は PlatformIO と指定のプラットフォームが必要です。
ビルドスクリプトは機体への書き込みを行いません。

過去の個人 PC パスや実機への導入結果は[履歴](history.md)にあります。
現在のチェックアウトに同じツール、成果物、機体が存在することを示すものではありません。
