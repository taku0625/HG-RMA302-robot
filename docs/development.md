# 開発環境とテスト

通常の走行操作は[README](../README.md)を参照してください。ここではUSB機器がないLinux環境での開発手順を説明します。

## 依存関係

Pythonは `.python-version` 指定の3.12、依存関係は `uv.lock` を使います。Linuxでは `evdev` のビルドにCコンパイラー、Python開発用ヘッダー、Linux入力ヘッダーが必要です。組み込みのホスト側試験には `cc`、C++試験には `g++` が必要です。

リポジトリのルートで実行します。

```bash
uv sync --frozen
uv pip check
```

クラウド環境ではホームのキャッシュ領域が書き込み不可で、Pythonの既定コンパイラー `clang` もないため、次を指定して導入します。

```bash
export UV_CACHE_DIR=/workspace/.cache/uv
export CC=gcc
export CXX=g++
cd /workspace/HG-RMA302-robot
uv sync --frozen
uv pip check
```

クラウドの既存チェックアウトを使います。作業ごとにGit worktreeを作る必要はありません。常駐サービスや追加の秘密情報は不要です。

## 実機なしで検証する

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m unittest discover -s embedded/tests -v
uv run --frozen hg-cart demo --config config.example.json
```

Pythonテストには疑似シリアルによるESC通信試験が含まれます。組み込みテストはSDKを模擬してCコードをコンパイルし、電源制御のメインループなどを実行します。デモの表示名は固定の入力例を表し、出力は設定したモードに依存します。配布例はジョイスティックなので、`left-wheel` 等の名前がそのまま実際の車輪の動作を表すとは限りません。

外部ソースなしで実行できるC++試験は次の2本です。

```bash
mkdir -p artifacts/validation/native
for name in current_sum_guard startup_lock; do
  g++ -std=c++17 -O2 -Wall -Wextra -Werror -Ifirmware \
    "tests/${name}_test.cpp" -o "artifacts/validation/native/${name}_test" || exit
  "artifacts/validation/native/${name}_test" || exit
done
```

残りのC++試験10本には、別のSTM32 ESCプロジェクトの `motor_control.hpp`、`motor_speed.hpp`、`motor_board_config.hpp` 等が必要です。このリポジトリだけでは実行できません。`firmware/*.patch` は外部プロジェクト向けの差分で、完全なESCソースではありません。

## クラウド環境での確認結果（2026-11-12）

- Python：176件中175件成功、1件スキップ。スキップは未収録の実機WT61キャプチャを使う試験です。
- 組み込みC：7件成功。
- 単独C++：2本成功。
- デモ、依存関係の整合性確認、`uv sync --frozen` の再実行：成功。
- 外部STM32ソースを要するC++試験10本、Pico／ESP32向けファームウェアビルド、実機走行・書き込み：未検証。

## ファームウェアをビルドする場合

[Pico／ESP32の手順](../embedded/README.md#ビルド)を参照してください。Pythonの実行環境とは別にPico SDK、ARM toolchain、CMake、picotoolが必要です。ESP32もビルドする場合はPlatformIOと指定のプラットフォームが必要です。ビルドスクリプトは機体への書き込みを行いません。

過去の個人PCパスや実機への導入結果は[履歴](history.md)にあります。現在のチェックアウトに同じツール、生成物、設定ファイルが存在することを示すものではありません。
