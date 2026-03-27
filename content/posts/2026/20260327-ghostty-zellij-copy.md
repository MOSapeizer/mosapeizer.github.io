+++
title = "Ghostty + Zellij 的一些坑"
date = "2026-03-27T10:00:00+08:00"
tags = ["ghostty", "zellij", "terminal"]
keywords = ["ghostty", "zellij", "copy", "cmd+c", "terminal multiplexer"]
description = "在 Ghostty 搭配 Zellij 使用時，Cmd+C 與 Alt 快捷鍵失效的原因與解法"
showFullContent = false
readingTime = false
hideComments = false
+++

## 問題

在 Ghostty 裡開 Zellij，按 Cmd+C 不會複製文字，反而會輸入大寫 `C`。

但不開 Zellij 的時候，Cmd+C 完全正常。

## 原因

鍵盤輸入的傳遞順序是這樣的：

```text
你 → Ghostty → Zellij → Shell
```

沒有 Zellij 時，Ghostty 會自己處理 Cmd+C，直接複製選取的文字到剪貼簿。

但當 Zellij 啟動後，它會使用 Kitty keyboard protocol 之類的協定，改變 Ghostty 傳送按鍵事件的方式。Ghostty 不再自己處理 Cmd+C，而是把原始的按鍵事件往下傳給 Zellij。而 Zellij 不認得這個組合鍵，就把它當成一般輸入處理了。

簡單來說：不是 Ghostty 不能處理 Cmd+C，而是 Zellij 的存在改變了 Ghostty 的行為。

## 解法

在 Ghostty 的設定檔 `~/.config/ghostty/config` 加上：

```ini
keybind = super+c=copy_to_clipboard
keybind = super+v=paste_from_clipboard
```

這會強制 Ghostty **永遠**自己處理 Cmd+C / Cmd+V，不管裡面跑的是什麼程式。

這跟 Ghostty 原本的行為完全一樣，只是把它寫成明確的設定，讓它的優先順序高於 Zellij。不會影響任何原有的功能。

改完之後重啟 Ghostty 就生效了。

## 問題二：Alt 快捷鍵無法使用

Zellij 的提示顯示可以用 Alt+F 切換浮動面板，但按下去沒反應。

### 原因

macOS 的 Option 鍵預設是用來輸入特殊字元的（例如 Option+F 會輸入 `ƒ`）。Ghostty 預設也會把 Option+Left/Right 映射成 `Esc+b`/`Esc+f`（單字跳轉），這跟 Zellij 的 Alt 快捷鍵直接衝突。

這是 Ghostty + Zellij 社群中[已知的問題](https://github.com/ghostty-org/ghostty/issues/3396)。

### 解法

在 `~/.config/ghostty/config` 加上：

```ini
macos-option-as-alt = left
```

這讓**左邊的 Option 鍵**變成 Alt（給 Zellij 用），**右邊的 Option 鍵**保持原本的特殊字元輸入功能。

## 問題三：中文輸入法 + Ctrl+C 會輸出亂碼（未解決）

在 Zellij 內用 Neovim，insert mode 輸入中文時一切正常，但在中文輸入法的狀態下按 Ctrl+C 想退出 insert mode，會輸出類似 `12559;5u` 的亂碼。切回英文輸入法再按就正常。

### 原因

`12559;5u` 是 Kitty keyboard protocol 的編碼格式。當輸入法有未送出的組字時按 Ctrl+C，Zellij 會把「Ctrl + 那個中文字的 Unicode codepoint」編碼成這串序列，Neovim 無法解讀就直接印出來了。

這是 Kitty keyboard protocol 與 IME 之間的[已知衝突](https://github.com/kovidgoyal/kitty/issues/4062)，Zellij 對這個協定的[實作也不完整](https://github.com/zellij-org/zellij/issues/4333)，目前沒有正式修復。

### 暫時的 workaround

退出 insert mode 前先切回英文輸入法，再按 Esc 或 Ctrl+C。

## 完整設定

最後 `~/.config/ghostty/config` 的內容：

```ini
keybind = super+c=copy_to_clipboard
keybind = super+v=paste_from_clipboard
macos-option-as-alt = left
```

重啟 Ghostty 就全部生效了。
