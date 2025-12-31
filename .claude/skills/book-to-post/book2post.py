#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests


# 極簡 slugify（避免多裝套件）；如果你想要更漂亮的 slug，可改用 python-slugify
def simple_slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s or "book"


@dataclass
class BookMeta:
    title: str = ""
    author: str = ""
    cover: str = ""
    description: str = ""
    isbn: str = ""
    publisher: str = ""
    published_date: str = ""
    google_books_url: str = ""


def search_google_books(query: str, is_isbn: bool = False) -> Optional[BookMeta]:
    """使用 Google Books API 搜尋書籍"""

    # 建立查詢
    if is_isbn:
        search_query = f"isbn:{query}"
    else:
        search_query = query

    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": search_query,
        "maxResults": 1,
        "langRestrict": "zh-TW|zh-CN|en",  # 優先中文和英文
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        if not data.get("items"):
            print(f"錯誤：找不到相關書籍 (查詢: {query})")
            return None

        # 取第一個結果
        item = data["items"][0]
        volume_info = item.get("volumeInfo", {})

        # 提取書籍資訊
        meta = BookMeta()
        meta.title = volume_info.get("title", "")

        # 作者可能是列表
        authors = volume_info.get("authors", [])
        meta.author = ", ".join(authors) if authors else ""

        # 封面圖片 - 優先使用大圖
        image_links = volume_info.get("imageLinks", {})
        meta.cover = (
            image_links.get("large") or
            image_links.get("medium") or
            image_links.get("thumbnail") or
            image_links.get("smallThumbnail") or
            ""
        )

        # 描述/簡介
        meta.description = volume_info.get("description", "")

        # ISBN
        identifiers = volume_info.get("industryIdentifiers", [])
        for identifier in identifiers:
            if identifier.get("type") in ("ISBN_13", "ISBN_10"):
                meta.isbn = identifier.get("identifier", "")
                break

        # 出版社和日期
        meta.publisher = volume_info.get("publisher", "")
        meta.published_date = volume_info.get("publishedDate", "")

        # Google Books 連結
        meta.google_books_url = volume_info.get("canonicalVolumeLink", "")

        return meta

    except requests.RequestException as e:
        print(f"錯誤：無法連接 Google Books API: {e}")
        return None
    except (json.JSONDecodeError, KeyError) as e:
        print(f"錯誤：解析 API 回應失敗: {e}")
        return None


def render_hugo_md(meta: BookMeta, page_title: Optional[str] = None) -> str:
    today = dt.date.today().isoformat()
    title = page_title or meta.title or "（未抓到書名）"

    def esc(s: str) -> str:
        return (s or "").replace('"', '\\"')

    # Front matter
    front_matter = f"""---
title: "{esc(title)}"
date: {today}
type: "books"
tags: ["reading"]
author: "{esc(meta.author)}"
isbn: "{esc(meta.isbn)}"
publisher: "{esc(meta.publisher)}"
published_date: "{esc(meta.published_date)}"
cover: "{esc(meta.cover)}"
google_books_url: "{esc(meta.google_books_url)}"
draft: true
---

"""

    # Body
    body = f"""## 書籍資訊

- **書名**：{meta.title or "（未抓到）"}
- **作者**：{meta.author or "（未抓到）"}
- **出版社**：{meta.publisher or "（未抓到）"}
- **出版日期**：{meta.published_date or "（未抓到）"}
- **ISBN**：{meta.isbn or "（未抓到）"}
- **Google Books**：{meta.google_books_url or "（未抓到）"}

## 簡介

{meta.description or "（未抓到）"}

## 讀後心得

（之後補）

## 筆記

-
"""
    return front_matter + body


def main():
    ap = argparse.ArgumentParser(
        description="使用 Google Books API 搜尋書籍並產生 Hugo 文章"
    )
    ap.add_argument("query", help="書名或 ISBN")
    ap.add_argument(
        "--isbn",
        action="store_true",
        help="將查詢視為 ISBN（預設為書名搜尋）"
    )
    ap.add_argument(
        "--outdir",
        default="content/books",
        help="輸出目錄（預設 content/books）"
    )
    ap.add_argument("--slug", default="", help="手動指定 slug（可選）")
    ap.add_argument("--title", default="", help="手動覆蓋文章 title（可選）")
    args = ap.parse_args()

    # 搜尋書籍
    print(f"正在搜尋: {args.query}...")
    meta = search_google_books(args.query, is_isbn=args.isbn)

    if not meta:
        raise SystemExit("搜尋失敗，請檢查查詢內容")

    print(f"找到書籍: {meta.title}")
    print(f"作者: {meta.author}")

    # 產生 slug
    slug = args.slug.strip() or simple_slugify(meta.title)

    # 建立輸出目錄
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 產生 Markdown
    md = render_hugo_md(meta, page_title=(args.title.strip() or None))
    outpath = outdir / f"{slug}.md"
    outpath.write_text(md, encoding="utf-8")

    print(f"\n成功！已寫入: {outpath}")


if __name__ == "__main__":
    main()
