+++
title = "你的 Zsh 為什麼這麼慢？從 2.2 秒優化到 0.5 秒"
date = "2026-03-29T09:00:00+08:00"
tags = ["zsh", "terminal", "performance", "dotfiles"]
keywords = ["zsh", "zshrc", "lazy loading", "conf.d", "shell startup", "optimization"]
description = "拆解 .zshrc 的啟動瓶頸，用 lazy loading 和模組化把 shell 開啟時間砍掉 75%"
showFullContent = false
readingTime = false
hideComments = false
+++

每次開新的終端機視窗，都要等一兩秒才看到 prompt 嗎？問題出在你的 `.zshrc`。

## 測量啟動時間

先量一下現狀：

```bash
/usr/bin/time zsh -i -c exit
```

我的結果是 **2.2 秒**。這代表每次開終端機都在等 2.2 秒，什麼事都沒做。

## 找出兇手

逐行計時：

```bash
# 個別測量每個 eval 的時間
echo -n "pyenv:  " && /usr/bin/time zsh -c 'eval "$(pyenv init -)"' 2>&1 | grep real
echo -n "nvm:    " && /usr/bin/time zsh -c 'source /usr/local/opt/nvm/nvm.sh' 2>&1 | grep real
echo -n "kubectl:" && /usr/bin/time zsh -c 'source <(kubectl completion zsh)' 2>&1 | grep real
```

我的排行榜：

| 項目               | 耗時  |
| ------------------ | ----- |
| codex completion   | 690ms |
| gvm                | 500ms |
| pyenv init         | 370ms |
| gh copilot alias   | 180ms |
| compinit           | 140ms |
| kubectl completion | 130ms |
| nvm.sh             | 110ms |

這些 `eval` 和 `source` 每次開 shell 都會跑，即使你根本沒用到那個工具。

## 解法一：Lazy Loading

核心概念：**用同名 function 取代 command，第一次呼叫時才載入真正的初始化。**

以 pyenv 為例，原本是這樣：

```zsh
# 每次開 shell 都跑，花 370ms
eval "$(pyenv init -)"
```

改成 lazy loading：

```zsh
pyenv() {
  unfunction pyenv                  # 1. 移除這個 wrapper
  eval "$(command pyenv init -)"    # 2. 載入真正的 pyenv
  pyenv "$@"                        # 3. 執行原本的指令
}
```

流程是這樣的：

1. **Shell 啟動** → 定義一個叫 `pyenv` 的 function（瞬間完成，只是定義）
2. **你打 `pyenv install 3.12`** → zsh 找到 `pyenv` function
3. **`unfunction pyenv`** → 把 wrapper 移除
4. **`eval "$(command pyenv init -)"`** → 載入真正的 pyenv（`command` 關鍵字會跳過 function，直接呼叫 binary）
5. **`pyenv "$@"`** → 現在 `pyenv` 是真的了，跑你原本的指令
6. **之後每次呼叫** → 直接走真正的 pyenv，wrapper 已經不在了

`"$@"` 負責把所有參數原封不動傳過去。

### NVM 比較麻煩

因為你不只會打 `nvm`，你還會直接打 `node`、`npm`、`npx`，所以要幫每個指令都做 wrapper：

```zsh
nvm() {
  unfunction nvm
  [ -s "/usr/local/opt/nvm/nvm.sh" ] && \. "/usr/local/opt/nvm/nvm.sh"
  nvm "$@"
}

node() {
  unfunction node npm npx 2>/dev/null
  [ -s "/usr/local/opt/nvm/nvm.sh" ] && \. "/usr/local/opt/nvm/nvm.sh"
  command node "$@"
}

npm() { node --version >/dev/null 2>&1; command npm "$@"; }
npx() { node --version >/dev/null 2>&1; command npx "$@"; }
```

`npm` 和 `npx` 會先觸發 `node`（載入 nvm），然後再執行自己。

### 其他工具同理

```zsh
# kubectl (~130ms)
kubectl() {
  unfunction kubectl
  source <(command kubectl completion zsh)
  command kubectl "$@"
}

# gvm (~500ms)
gvm() {
  unfunction gvm
  [[ -s "$HOME/.gvm/scripts/gvm" ]] && source "$HOME/.gvm/scripts/gvm"
  gvm "$@"
}

# codex (~690ms)
codex() {
  unfunction codex
  eval "$(command codex completion zsh)"
  command codex "$@"
}
```

套用 lazy loading 後：**2.2 秒 → 0.55 秒**。

## 解法二：模組化 .zshrc

`.zshrc` 越長越難維護。借用 Unix 的 `conf.d` 模式來拆分。

### conf.d 模式

你在很多地方都能看到這個模式：

- `/etc/nginx/conf.d/` — Nginx 設定
- `/etc/profile.d/` — 系統 shell scripts
- `/etc/cron.d/` — cron jobs

概念很簡單：不要一個巨大的設定檔，改成一個資料夾裡放很多小檔案，系統自動全部載入。

### 實作

建立資料夾結構：

```
~/.zsh/conf.d/
  01-completion.zsh   ← compinit、fpath
  02-exports.zsh      ← 環境變數
  03-path.zsh         ← 所有 PATH 設定
  04-aliases.zsh      ← 快捷指令
  05-lazy.zsh         ← lazy loading wrappers
  06-plugins.zsh      ← autosuggestions、syntax-highlighting、starship
  07-peco.zsh         ← peco 快捷鍵綁定
  08-vendor.zsh       ← gcloud、nix、dart 等第三方
```

`.zshrc` 只剩三行：

```zsh
for conf in ~/.zsh/conf.d/*.zsh; do
  source "$conf"
done
```

### 編號 = 相依順序

唯一的規則：**如果 A 依賴 B，B 的編號要比較小。**

- `03-path.zsh` 用到 `$PYENV_ROOT` → `02-exports.zsh` 要先載入
- `05-lazy.zsh` 包裝的指令需要在 `$PATH` 裡 → 排在 `03-path.zsh` 後面
- `06-plugins.zsh` 有 starship prompt → 排在修改 shell 的東西之後

兩個檔案如果互不相依，順序無所謂。

### 好處

- **好找**：想改 alias？打開 `04-aliases.zsh`
- **好加**：新工具就丟一個新 `.zsh` 進去
- **好刪**：不用某個工具了，刪掉那個檔案就好
- **好分享**：可以只分享某幾個模組

## 額外收穫：硬編碼取代 subshell

這些每次都在跑 subprocess，但結果永遠一樣：

```zsh
# 之前（每次跑 subprocess）
export JAVA_HOME=$(/usr/libexec/java_home -v 1.8)
source $(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh

# 之後（直接寫死路徑）
export JAVA_HOME="/Library/Java/JavaVirtualMachines/jdk1.8.0_191.jdk/Contents/Home"
source /usr/local/share/zsh-autosuggestions/zsh-autosuggestions.zsh
```

`brew --prefix` 每次要跑 100-200ms，但它永遠回傳 `/usr/local`。直接寫死就好。

## 結果

|             | 優化前     | 優化後     |
| ----------- | ---------- | ---------- |
| 啟動時間    | 2.2 秒     | 0.55 秒    |
| .zshrc 行數 | 167 行     | 3 行       |
| 模組數      | 1 個大檔案 | 8 個小檔案 |

第一次用到某個工具時會有一次性的載入延遲，之後就跟原本一樣快。大部分時候你開 shell 根本不會用到全部的工具，所以這些時間就省下來了。
