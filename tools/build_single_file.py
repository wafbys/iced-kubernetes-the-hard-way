#!/usr/bin/env python3
"""把 docs/zh/00-13 章与术语表合成一个自包含 HTML（可选内嵌字体）。

用法:
    python tools/build_single_file.py                 # 生成到 docs/zh/kubernetes-the-hard-way-zh.html
    python tools/build_single_file.py --out out.html  # 指定输出
    python tools/build_single_file.py --no-fonts      # 不内嵌字体（依赖本机已安装字体）

内嵌字体需要本机安装以下字体，并需要 `pip install fonttools brotli`：
    sans  : Inter              (InterVariable.ttf)
    serif : Source Serif 4     (SourceSerif4-VariableFont_opsz,wght.ttf)
    mono  : New Computer Modern Mono 10 (NewCMMono10-Regular.otf / -Bold.otf)
    CJK   : KingHwaOldSong-GB  (京華老宋体-GB.ttf)
字体文件在 FONT_DIRS 中按 FONT_FILES 的候选名查找，找不到就跳过该字体、退回本机字体。
"""
import argparse
import base64
import html
import io
import re
import subprocess
import sys
from pathlib import Path

import markdown
from markdown.extensions.toc import slugify_unicode

ROOT = Path(__file__).resolve().parents[1]
ZH = ROOT / "docs" / "zh"

# 字体候选目录与文件：(CSS 家族名, 说明, 候选文件名, 静态字重, 是否变量字体)
FONT_DIRS = [
    Path(r"C:\Windows\Fonts"),
    Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts",
]
FONT_FILES = [
    ("Inter", "Inter Variable", ["InterVariable.ttf"], "100 900", True),
    ("Source Serif 4", "Source Serif 4 Variable",
     ["SourceSerif4-VariableFont_opsz,wght.ttf"], "200 900", True),
    ("NewComputerModern Mono 10", "NewCM Mono Regular", ["NewCMMono10-Regular.otf"], "400", False),
    ("NewComputerModern Mono 10", "NewCM Mono Bold", ["NewCMMono10-Bold.otf"], "700", False),
    ("KingHwaOldSong-GB", "京華老宋体-GB", ["京華老宋体-GB.ttf", "KingHwaOldSong-GB.ttf"], "400", False),
]

# 主题：(id, 下拉显示名, CSS 变量覆盖)。anthropic 为默认（完整取值写在 :root 中），覆盖项留空。
THEMES = [
    ("anthropic", "Anthropic · Claude", {}),
    ("openai", "OpenAI · ChatGPT", {
        "heading": "var(--sans)",
        "sidebar-bg": "#F7F7F8",
        "bg": "#FFFFFF", "bg-soft": "#F7F7F8", "surface": "#FFFFFF",
        "text": "#0D0D0D", "muted": "#6E6E80", "faint": "#8E8EA0",
        "accent": "#10A37F", "accent-strong": "#0E8C6D", "accent-soft": "#E6F4F0", "on-accent": "#FFFFFF",
        "border": "#E5E5E5", "border-strong": "#D0D0D0",
        "code-bg": "#0D0D0D", "code-text": "#ECECF1", "code-inline-fg": "#0E8C6D", "code-border": "transparent",
        "code-control-bg": "rgba(255,255,255,.1)", "code-control-fg": "#ECECF1",
        "code-control-border": "rgba(255,255,255,.18)", "code-control-hover": "rgba(255,255,255,.22)",
        "code-label": "rgba(236,236,241,.45)",
        "shadow": "0 1px 2px rgba(13,13,13,.05),0 10px 30px rgba(13,13,13,.06)",
        "quote-text": "#40414F",
        "r-xs": "4px", "r-sm": "8px", "r-md": "12px", "r-lg": "14px",
    }),
    ("google", "Google · Material", {
        "heading": "var(--sans)",
        "sans": '"Google Sans","Product Sans","Roboto","Inter",var(--cjk),sans-serif',
        "sidebar-bg": "#F8F9FA",
        "bg": "#FFFFFF", "bg-soft": "#F1F3F4", "surface": "#FFFFFF",
        "text": "#202124", "muted": "#5F6368", "faint": "#80868B",
        "accent": "#1A73E8", "accent-strong": "#1557B0", "accent-soft": "#E8F0FE", "on-accent": "#FFFFFF",
        "border": "#DADCE0", "border-strong": "#BDC1C6",
        "code-bg": "#F8F9FA", "code-text": "#202124", "code-inline-fg": "#1967D2", "code-border": "#DADCE0",
        "code-control-bg": "rgba(32,33,36,.06)", "code-control-fg": "#5F6368",
        "code-control-border": "rgba(32,33,36,.12)", "code-control-hover": "rgba(32,33,36,.12)",
        "code-label": "rgba(32,33,36,.45)",
        "shadow": "0 1px 2px rgba(60,64,67,.1),0 2px 6px rgba(60,64,67,.08)",
        "quote-text": "#3C4043",
        "r-xs": "4px", "r-sm": "8px", "r-md": "8px", "r-lg": "12px",
    }),
    ("microsoft", "Microsoft · Fluent", {
        "heading": "var(--sans)",
        "sans": '"Segoe UI","Inter","Helvetica Neue",Arial,var(--cjk),sans-serif',
        "sidebar-bg": "#F3F2F1",
        "bg": "#FFFFFF", "bg-soft": "#F3F2F1", "surface": "#FFFFFF",
        "text": "#201F1E", "muted": "#605E5C", "faint": "#8A8886",
        "accent": "#0078D4", "accent-strong": "#005A9E", "accent-soft": "#DEECF9", "on-accent": "#FFFFFF",
        "border": "#EDEBE9", "border-strong": "#D2D0CE",
        "code-bg": "#F3F2F1", "code-text": "#201F1E", "code-inline-fg": "#005A9E", "code-border": "#E1DFDD",
        "code-control-bg": "rgba(32,31,30,.06)", "code-control-fg": "#605E5C",
        "code-control-border": "rgba(32,31,30,.12)", "code-control-hover": "rgba(32,31,30,.12)",
        "code-label": "rgba(32,31,30,.45)",
        "shadow": "0 1.6px 3.6px rgba(0,0,0,.08),0 .3px .9px rgba(0,0,0,.06)",
        "quote-text": "#323130",
        "r-xs": "2px", "r-sm": "4px", "r-md": "4px", "r-lg": "6px",
    }),
    ("apple", "Apple · HIG", {
        "heading": "var(--sans)",
        "sans": '-apple-system,"SF Pro Text","SF Pro Display","Helvetica Neue","Inter",var(--cjk),sans-serif',
        "sidebar-bg": "linear-gradient(180deg,#F5F5F7,#EFEFF2)",
        "bg": "#FBFBFD", "bg-soft": "#F5F5F7", "surface": "#FFFFFF",
        "text": "#1D1D1F", "muted": "#6E6E73", "faint": "#86868B",
        "accent": "#0071E3", "accent-strong": "#0066CC", "accent-soft": "#E8F2FF", "on-accent": "#FFFFFF",
        "border": "#D2D2D7", "border-strong": "#C6C6C9",
        "code-bg": "#1D1D1F", "code-text": "#F5F5F7", "code-inline-fg": "#0066CC", "code-border": "transparent",
        "code-control-bg": "rgba(255,255,255,.12)", "code-control-fg": "#F5F5F7",
        "code-control-border": "rgba(255,255,255,.2)", "code-control-hover": "rgba(255,255,255,.24)",
        "code-label": "rgba(245,245,247,.45)",
        "shadow": "0 2px 8px rgba(0,0,0,.06),0 12px 32px rgba(0,0,0,.06)",
        "quote-text": "#424245",
        "r-xs": "6px", "r-sm": "10px", "r-md": "16px", "r-lg": "20px",
    }),
    ("github", "GitHub", {
        "heading": "var(--sans)",
        "sidebar-bg": "#F6F8FA",
        "bg": "#FFFFFF", "bg-soft": "#F6F8FA", "surface": "#FFFFFF",
        "text": "#1F2328", "muted": "#59636E", "faint": "#818B98",
        "accent": "#0969DA", "accent-strong": "#0757B8", "accent-soft": "#DDF4FF", "on-accent": "#FFFFFF",
        "border": "#D0D7DE", "border-strong": "#AFB8C1",
        "code-bg": "#F6F8FA", "code-text": "#1F2328", "code-inline-fg": "#1F2328", "code-border": "#D0D7DE",
        "code-control-bg": "rgba(31,35,40,.06)", "code-control-fg": "#57606A",
        "code-control-border": "rgba(31,35,40,.12)", "code-control-hover": "rgba(31,35,40,.12)",
        "code-label": "rgba(31,35,40,.45)",
        "shadow": "0 1px 0 rgba(31,35,40,.04),0 3px 6px rgba(140,149,159,.15)",
        "quote-text": "#59636E",
        "r-xs": "6px", "r-sm": "6px", "r-md": "6px", "r-lg": "6px",
    }),
    ("stripe", "Stripe", {
        "heading": "var(--sans)",
        "sidebar-bg": "linear-gradient(180deg,#F6F9FC,#EEF3F9)",
        "bg": "#FFFFFF", "bg-soft": "#F6F9FC", "surface": "#FFFFFF",
        "text": "#0A2540", "muted": "#425466", "faint": "#697386",
        "accent": "#635BFF", "accent-strong": "#4F46E5", "accent-soft": "#EFEEFF", "on-accent": "#FFFFFF",
        "border": "#E6EBF1", "border-strong": "#D6DEE8",
        "code-bg": "#0A2540", "code-text": "#E6EBF1", "code-inline-fg": "#635BFF", "code-border": "transparent",
        "code-control-bg": "rgba(255,255,255,.1)", "code-control-fg": "#E6EBF1",
        "code-control-border": "rgba(255,255,255,.18)", "code-control-hover": "rgba(255,255,255,.22)",
        "code-label": "rgba(230,235,241,.45)",
        "shadow": "0 2px 5px rgba(50,50,93,.08),0 8px 24px rgba(50,50,93,.08)",
        "quote-text": "#425466",
        "r-xs": "4px", "r-sm": "8px", "r-md": "10px", "r-lg": "16px",
    }),
    ("vercel", "Vercel · 黑白", {
        "color-scheme": "dark",
        "heading": "var(--sans)",
        "sidebar-bg": "#0A0A0A",
        "bg": "#000000", "bg-soft": "#0F0F0F", "surface": "#0A0A0A",
        "text": "#EDEDED", "muted": "#A1A1A1", "faint": "#7A7A7A",
        "accent": "#FFFFFF", "accent-strong": "#FFFFFF", "accent-soft": "#1A1A1A", "on-accent": "#000000",
        "border": "#1F1F1F", "border-strong": "#333333",
        "code-bg": "#000000", "code-text": "#EDEDED", "code-inline-fg": "#FFFFFF", "code-border": "#333333",
        "code-control-bg": "rgba(255,255,255,.1)", "code-control-fg": "#EDEDED",
        "code-control-border": "rgba(255,255,255,.2)", "code-control-hover": "rgba(255,255,255,.24)",
        "code-label": "rgba(237,237,237,.45)",
        "shadow": "0 1px 2px rgba(0,0,0,.6),0 10px 30px rgba(0,0,0,.6)",
        "quote-text": "#B5B5B5",
        "r-xs": "2px", "r-sm": "4px", "r-md": "6px", "r-lg": "8px",
    }),
]
REPO = "https://github.com/wafbys/iced-kubernetes-the-hard-way"
BLOB = REPO + "/blob/main/"

CHAPTERS = [
    ("00", "00-debian-install.md", "环境准备：安装 Debian"),
    ("01", "01-prerequisites.md", "前提条件"),
    ("02", "02-jumpbox.md", "设置跳板机"),
    ("03", "03-compute-resources.md", "准备计算资源"),
    ("04", "04-certificate-authority.md", "准备 CA 并生成 TLS 证书"),
    ("05", "05-kubernetes-configuration-files.md", "生成用于认证的 Kubernetes 配置文件"),
    ("06", "06-data-encryption-keys.md", "生成数据加密配置与密钥"),
    ("07", "07-bootstrapping-etcd.md", "引导 etcd 集群"),
    ("08", "08-bootstrapping-kubernetes-controllers.md", "引导 Kubernetes 控制平面"),
    ("09", "09-bootstrapping-kubernetes-workers.md", "引导 Kubernetes 工作节点"),
    ("10", "10-configuring-kubectl.md", "配置 kubectl 远程访问"),
    ("11", "11-pod-network-routes.md", "配置 Pod 网络路由"),
    ("12", "12-smoke-test.md", "冒烟测试"),
    ("13", "13-cleanup.md", "清理"),
]
CH_BY_FILE = {fn: num for num, fn, _ in CHAPTERS}

CJK = r"\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef"
JOIN_CJK = re.compile(rf"(?<=[{CJK}])[ \t]*\n[ \t]*(?:>[ \t]*)?(?=[{CJK}])")
FENCE = re.compile(r"(```.*?```)", re.S)
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
META_COMMENT = re.compile(r"\A\s*<!--.*?-->\s*", re.S)
H1 = re.compile(r"<h1[^>]*>\s*(\d{2})\s*-\s*([^<]+?)</h1>")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def rewrite_links(text: str) -> str:
    def repl(m: re.Match) -> str:
        label, target = m.group(1), m.group(2)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            return m.group(0)
        frag = ""
        if "#" in target:
            target, frag = target.split("#", 1)
            frag = "#" + frag
        name = Path(target).name
        if name in CH_BY_FILE:
            return f"[{label}](#chapter-{CH_BY_FILE[name]}{frag})"
        if target.endswith("README.md") or target.startswith("../"):
            depth = 0
            rest = target
            while rest.startswith("../"):
                depth += 1
                rest = rest[3:]
            base = ZH
            for _ in range(depth):
                base = base.parent
            repo_file = (base / rest).resolve()
            try:
                rel = repo_file.relative_to(ROOT).as_posix()
            except ValueError:
                rel = rest
            return f"[{label}]({BLOB}{rel}{frag})"
        return m.group(0)

    return LINK.sub(repl, text)


def process_prose(text: str) -> str:
    parts = FENCE.split(text)
    for i in range(0, len(parts), 2):
        parts[i] = rewrite_links(JOIN_CJK.sub("", parts[i]))
    return "".join(parts)


def convert(text: str, chapter: str) -> tuple[str, list]:
    md = markdown.Markdown(
        extensions=["extra", "toc", "sane_lists"],
        extension_configs={
            "toc": {
                "slugify": lambda value, separator: f"c{chapter}-{slugify_unicode(value, separator)}",
                "toc_depth": "2-3",
            }
        },
    )
    body = md.convert(text)
    return body, md.toc_tokens


def nav_tokens(tokens: list) -> str:
    out = []

    def walk(items):
        for t in items:
            lvl = t["level"]
            cls = "toc-sub" if lvl == 2 else "toc-sub2"
            out.append(f'<a class="{cls}" href="#{t["id"]}">{html.escape(t["name"])}</a>')
            if t.get("children"):
                walk(t["children"])

    walk(tokens)
    return "\n      ".join(out)


def find_font(candidates: list) -> Path | None:
    for d in FONT_DIRS:
        for name in candidates:
            p = d / name
            if p.exists():
                return p
    return None


def weight_range(path: Path) -> str | None:
    from fontTools.ttLib import TTFont

    f = TTFont(str(path), lazy=True)
    try:
        if "fvar" in f:
            for axis in f["fvar"].axes:
                if axis.axisTag == "wght":
                    return f"{int(axis.minValue)} {int(axis.maxValue)}"
    finally:
        f.close()
    return None


def subset_woff2(path: Path, chars) -> bytes:
    from fontTools import subset as ftsubset

    options = ftsubset.Options()
    options.flavor = "woff2"
    options.hinting = False
    options.desubroutinize = False
    options.layout_features = ["*"]
    options.notdef_outline = True
    options.drop_tables += ["DSIG", "EBDT", "EBLC", "EBSC", "SVG "]
    font = ftsubset.load_font(str(path), options)
    ss = ftsubset.Subsetter(options=options)
    ss.populate(text="".join(sorted(chars)))
    ss.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    font.close()
    return buf.getvalue()


def build_font_faces(doc: str):
    """按文档实际用到的字符为各字体做子集，生成 @font-face 规则。"""
    latin_chars = set(doc)
    cjk_chars = {c for c in latin_chars if ord(c) >= 0x2E80}
    faces, notes = [], []
    for family, label, candidates, default_weight, variable in FONT_FILES:
        path = find_font(candidates)
        if path is None:
            notes.append(f"  ! 未找到 {label}（{candidates[0]}），跳过内嵌")
            continue
        chars = cjk_chars if family.startswith("KingHwa") else latin_chars
        data = subset_woff2(path, chars)
        weight = (weight_range(path) if variable else None) or default_weight
        b64 = base64.b64encode(data).decode("ascii")
        faces.append(
            f'@font-face{{font-family:"{family}";font-style:normal;font-weight:{weight};'
            f'src:url(data:font/woff2;base64,{b64}) format("woff2")}}'
        )
        notes.append(f"  - {label}: {path.name} → {len(data)/1024:.0f} KiB（{len(chars)} 字符）")
    return "\n".join(faces), notes


def main() -> None:
    ap = argparse.ArgumentParser(description="生成 Kubernetes The Hard Way 中文单文件 HTML")
    ap.add_argument("--out", default=str(ZH / "kubernetes-the-hard-way-zh.html"), help="输出 HTML 路径")
    ap.add_argument("--no-fonts", action="store_true", help="不内嵌字体")
    args = ap.parse_args()
    out = Path(args.out)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
        capture_output=True, text=True,
    ).stdout.strip() or "unknown"

    chapters_html, nav_html = [], []
    for num, fn, short in CHAPTERS:
        raw = META_COMMENT.sub("", read_text(ZH / fn))
        body, tokens = convert(process_prose(raw), num)
        body = H1.sub(
            lambda m: f'<header class="chapter-head"><span class="chapter-num">{m.group(1)}</span><h1>{m.group(2).strip()}</h1></header>',
            body, count=1,
        )
        chapters_html.append(f'<section id="chapter-{num}" class="chapter">\n{body}\n</section>')
        subs = nav_tokens(tokens)
        nav_html.append(
            f'<div class="toc-group">\n'
            f'      <a class="toc-chapter" href="#chapter-{num}"><span class="toc-num">{num}</span>{html.escape(short)}</a>\n'
            f'      {subs}\n'
            f'    </div>'
        )

    # 附录：术语表
    raw = META_COMMENT.sub("", read_text(ROOT / "reference" / "glossary.md"))
    g_body, g_tokens = convert(process_prose(raw), "glossary")
    g_body = re.sub(
        r"<h1[^>]*>.*?</h1>",
        '<header class="chapter-head"><span class="chapter-num">附录</span><h1>术语表（English → 中文）</h1></header>',
        g_body, count=1, flags=re.S,
    )
    g_html = f'<section id="glossary" class="chapter">\n{g_body}\n</section>'

    # 代码块语言标签
    def lang(m: re.Match) -> str:
        return f'<pre data-lang="{m.group(1)}"><code class="language-{m.group(1)}"'

    for i, block in enumerate(chapters_html):
        chapters_html[i] = re.sub(r'<pre><code class="language-([a-zA-Z0-9]+)"', lang, block)
    g_html = re.sub(r'<pre><code class="language-([a-zA-Z0-9]+)"', lang, g_html)

    # “下一节”段落样式
    def nextlink(s: str) -> str:
        return re.sub(r"<p>(下一节：.*?)</p>", r'<p class="next-link">\1</p>', s, flags=re.S)

    chapters_html = [nextlink(c) for c in chapters_html]
    g_html = nextlink(g_html)

    toc = (
        '<a class="toc-cover" href="#cover">封面与说明</a>\n    '
        + "\n    ".join(nav_html)
        + '\n    <a class="toc-cover" href="#glossary">附录 · 术语表</a>'
    )

    themes_css = "\n".join(
        f'html[data-theme="{tid}"]{{' + "".join(f"{k}:{v};" for k, v in ov.items()) + "}"
        for tid, _label, ov in THEMES if ov
    )
    theme_options = "\n    ".join(
        f'<option value="{tid}">{label}</option>' for tid, label, _ in THEMES
    )

    doc = TEMPLATE.format(
        repo=REPO,
        commit=commit,
        toc=toc,
        themes=themes_css,
        theme_options=theme_options,
        content="\n\n".join(chapters_html) + "\n\n" + g_html,
    )
    if not args.no_fonts:
        faces, notes = build_font_faces(doc)
        if faces:
            doc = doc.replace("<style>", "<style>\n" + faces, 1)
        print("内嵌字体：")
        for n in notes:
            print(n)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    print(f"written: {out}")
    print(f"size: {out.stat().st_size / 1024:.1f} KiB")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>Kubernetes The Hard Way · 中文单文件版</title>
<meta name="description" content="Kubernetes The Hard Way 中文版 —— 00 至 13 章与术语表的自包含单文件 HTML。">
<style>
:root{{
  --sidebar:300px;
  --cjk:"KingHwaOldSong-GB","Songti SC","SimSun";
  --serif:"Source Serif 4","Source Serif Pro","Source Serif 4 Variable",Georgia,"Times New Roman",var(--cjk),serif;
  --sans:"Inter","Inter Variable","Segoe UI",Roboto,"Helvetica Neue",Arial,var(--cjk),sans-serif;
  --mono:"NewComputerModern Mono 10","New Computer Modern Mono","NewCM10-Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,"Cascadia Code",var(--cjk),monospace;
  --heading:var(--serif);
  --r-xs:6px; --r-sm:10px; --r-md:14px; --r-lg:16px;
  --sidebar-bg:linear-gradient(180deg,#F6F2E9,#F0ECE1);
  --bg:#FAF9F5; --bg-soft:#F0EEE6; --surface:#FFFFFF;
  --text:#1F1E1D; --muted:#6B6862; --faint:#918B80;
  --accent:#D97757; --accent-strong:#BC5B39; --accent-soft:#F4E4DC; --on-accent:#FFFFFF;
  --border:#E6E1D6; --border-strong:#D9D3C5;
  --code-bg:#262523; --code-text:#ECE9E2; --code-inline-fg:#4A3B34; --code-border:transparent;
  --code-control-bg:rgba(255,255,255,.09); --code-control-fg:#EDEBE4;
  --code-control-border:rgba(255,255,255,.16); --code-control-hover:rgba(255,255,255,.22);
  --code-label:rgba(236,233,226,.42);
  --shadow:0 1px 2px rgba(31,30,29,.05),0 10px 30px rgba(31,30,29,.06);
  --quote-text:#4A4844;
  color-scheme:light;
}}
{themes}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);font-size:16px;line-height:1.85;-webkit-font-smoothing:antialiased}}
a{{color:inherit}}
code,pre,samp,kbd{{font-family:var(--mono)}}
:not(pre)>code{{background:var(--bg-soft);border:1px solid var(--border);border-radius:var(--r-xs);padding:.1em .42em;color:var(--code-inline-fg)}}

/* ---------- 侧栏 ---------- */
.sidebar{{position:fixed;top:0;bottom:0;left:0;width:var(--sidebar);display:flex;flex-direction:column;background:var(--sidebar-bg);border-right:1px solid var(--border);z-index:40}}
.brand{{display:flex;gap:12px;align-items:center;padding:22px 20px 14px}}
.brand-mark{{flex:none;width:40px;height:40px;border-radius:var(--r-md);background:var(--accent);color:var(--on-accent);font-weight:700;font-size:13px;display:grid;place-items:center;letter-spacing:.5px;box-shadow:var(--shadow)}}
.brand-title{{font-family:var(--heading);font-size:16px;font-weight:600;line-height:1.25}}
.brand-sub{{font-size:11.5px;color:var(--muted);margin-top:3px;letter-spacing:.3px}}
.theme-bar{{margin:0 18px 8px;display:flex;align-items:center;gap:8px}}
.theme-bar label{{font-size:11px;color:var(--faint);letter-spacing:.6px;flex:none}}
.theme-bar select{{flex:1;min-width:0;padding:7px 10px;border:1px solid var(--border-strong);border-radius:var(--r-sm);background:var(--surface);color:var(--text);font-family:inherit;font-size:12.5px}}
.theme-bar select:focus{{outline:2px solid var(--accent-soft);border-color:var(--accent)}}
.filter{{margin:0 18px 10px;padding:9px 12px;border:1px solid var(--border-strong);border-radius:var(--r-sm);background:var(--surface);font-family:inherit;font-size:13px;color:var(--text)}}
.filter:focus{{outline:2px solid var(--accent-soft);border-color:var(--accent)}}
.toc{{flex:1;overflow-y:auto;padding:4px 12px 18px}}
.toc a{{display:block;text-decoration:none;color:var(--muted);font-size:13px;line-height:1.45;padding:5px 10px;border-radius:var(--r-sm)}}
.toc a:hover{{background:color-mix(in srgb,var(--accent) 12%,transparent);color:var(--text)}}
.toc a.active{{background:var(--accent-soft);color:var(--accent-strong);font-weight:600}}
.toc .toc-cover{{font-weight:600;color:var(--text);margin:2px 0 6px}}
.toc .toc-chapter{{margin-top:8px;font-weight:600;color:var(--text);font-size:13.5px}}
.toc .toc-num{{display:inline-block;min-width:1.9em;color:var(--accent);font-variant-numeric:tabular-nums;font-weight:700}}
.toc .toc-sub{{padding-left:30px;font-size:12.5px}}
.toc .toc-sub2{{padding-left:44px;font-size:12px;color:var(--faint)}}
.toc-group{{margin-bottom:2px}}
.toc-hidden{{display:none !important}}
.sidebar-foot{{padding:12px 20px;border-top:1px solid var(--border);font-size:11px;color:var(--faint);line-height:1.6}}
.sidebar-foot a{{color:var(--muted)}}

/* ---------- 正文 ---------- */
.progress{{position:fixed;top:0;left:var(--sidebar);right:0;height:3px;z-index:60;pointer-events:none}}
.progress span{{display:block;height:100%;width:0;background:var(--accent)}}
.content{{margin-left:var(--sidebar);padding:0 48px 90px;max-width:1120px}}
.cover{{max-width:840px;padding:76px 0 42px;border-bottom:1px solid var(--border);scroll-margin-top:20px}}
.eyebrow{{font-size:12.5px;letter-spacing:2.2px;text-transform:uppercase;color:var(--accent-strong);font-weight:600}}
.cover h1{{font-family:var(--heading);font-size:clamp(34px,5vw,52px);line-height:1.08;letter-spacing:-.6px;margin:16px 0 12px}}
.lede{{font-size:17.5px;color:var(--muted);max-width:660px;margin:0}}
.meta-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px;margin:30px 0 10px}}
.meta-card{{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg);padding:13px 16px;box-shadow:var(--shadow)}}
.meta-card dt{{font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:var(--faint);margin:0 0 5px}}
.meta-card dd{{margin:0;font-size:13.5px;line-height:1.6}}
.callout{{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:0 var(--r-md) var(--r-md) 0;padding:14px 18px;margin:16px 0;color:var(--quote-text);font-size:14px;line-height:1.75}}
.callout a{{color:var(--accent-strong)}}
kbd{{font-family:var(--mono);font-size:12px;background:var(--bg-soft);border:1px solid var(--border-strong);border-bottom-width:2px;border-radius:var(--r-xs);padding:1px 6px}}

.chapter{{max-width:840px;padding-top:54px;scroll-margin-top:10px}}
.chapter-head{{display:flex;align-items:baseline;gap:14px;margin:0 0 4px}}
.chapter-num{{flex:none;font-family:var(--heading);font-size:14px;font-weight:700;color:var(--on-accent);background:var(--accent);border-radius:var(--r-sm);padding:5px 11px;letter-spacing:1px}}
.chapter-head h1{{margin:0;font-family:var(--heading);font-size:clamp(28px,3.6vw,36px);line-height:1.2;letter-spacing:-.4px}}
.chapter h2{{font-family:var(--heading);font-size:24px;line-height:1.3;margin:2.3em 0 .7em;padding-top:1.3em;border-top:1px solid var(--border)}}
.chapter h3{{font-family:var(--heading);font-size:19.5px;margin:1.9em 0 .5em}}
.chapter h4{{font-size:15.5px;margin:1.5em 0 .4em}}
h1,h2,h3,h4{{scroll-margin-top:22px}}
.chapter p{{margin:.85em 0}}
.chapter a{{color:var(--accent-strong);text-decoration:none;border-bottom:1px solid color-mix(in srgb,var(--accent-strong) 32%,transparent)}}
.chapter a:hover{{border-bottom-color:var(--accent-strong)}}
.chapter strong{{font-weight:650}}
.chapter ul,.chapter ol{{padding-left:1.45em;margin:.85em 0}}
.chapter li{{margin:.35em 0}}
.chapter li::marker{{color:var(--accent)}}
.chapter hr{{border:0;border-top:1px solid var(--border);margin:2em 0}}
blockquote{{margin:1.2em 0;padding:.75em 1.15em;background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);border-radius:0 var(--r-md) var(--r-md) 0;color:var(--quote-text)}}
blockquote p{{margin:.3em 0}}
.chapter code{{font-family:var(--mono);font-size:.85em;background:var(--bg-soft);border:1px solid var(--border);border-radius:var(--r-xs);padding:.12em .4em;color:var(--code-inline-fg);white-space:nowrap}}
.chapter pre{{position:relative;background:var(--code-bg);color:var(--code-text);border:1px solid var(--code-border);border-radius:var(--r-lg);padding:40px 20px 18px;overflow:auto;margin:1.25em 0;box-shadow:var(--shadow);line-height:1.65}}
.chapter pre code{{display:block;background:none;border:0;padding:0;color:inherit;font-size:13.5px;white-space:pre;font-family:var(--mono)}}
.chapter pre[data-lang]::before{{content:attr(data-lang);position:absolute;top:12px;left:16px;font-size:10.5px;letter-spacing:1.4px;text-transform:uppercase;color:var(--code-label)}}
.chapter pre::-webkit-scrollbar{{height:10px;width:10px}}
.chapter pre::-webkit-scrollbar-thumb{{background:var(--code-control-border);border-radius:6px}}
.copy-btn{{position:absolute;top:9px;right:10px;background:var(--code-control-bg);color:var(--code-control-fg);border:1px solid var(--code-control-border);border-radius:var(--r-xs);padding:4px 10px;font-family:var(--sans);font-size:11.5px;cursor:pointer;opacity:0;transition:opacity .15s,background .15s}}
.chapter pre:hover .copy-btn,.copy-btn:focus{{opacity:1}}
.copy-btn:hover{{background:var(--code-control-hover)}}

.chapter table{{width:100%;border-collapse:collapse;margin:1.25em 0;font-size:13.8px;background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);overflow:hidden}}
.chapter th{{background:var(--bg-soft);text-align:left;font-weight:650;color:var(--text)}}
.chapter th,.chapter td{{padding:10px 14px;border-bottom:1px solid var(--border);vertical-align:top}}
.chapter tr:last-child td{{border-bottom:0}}

.next-link{{display:inline-block;margin-top:14px !important;padding:10px 16px;background:var(--accent-soft);border-radius:var(--r-md);color:var(--accent-strong)}}
.next-link a{{border-bottom:0}}

.page-foot{{max-width:840px;margin-top:64px;padding-top:22px;border-top:1px solid var(--border);color:var(--faint);font-size:12.5px;line-height:1.8}}
.page-foot a{{color:var(--muted)}}

.to-top{{position:fixed;right:26px;bottom:26px;width:44px;height:44px;border-radius:50%;border:1px solid var(--border-strong);background:var(--surface);color:var(--text);font-size:18px;cursor:pointer;box-shadow:var(--shadow);opacity:0;pointer-events:none;transition:opacity .2s,transform .2s;z-index:50}}
.to-top.show{{opacity:1;pointer-events:auto}}
.to-top:hover{{transform:translateY(-2px)}}
.menu-toggle{{display:none;position:fixed;top:14px;left:14px;width:42px;height:42px;border-radius:var(--r-md);border:1px solid var(--border-strong);background:var(--surface);font-size:18px;cursor:pointer;box-shadow:var(--shadow);z-index:70}}

@media (max-width:1000px){{
  .content{{margin-left:0;padding:0 22px 80px}}
  .sidebar{{transform:translateX(-100%);transition:transform .22s ease;box-shadow:var(--shadow)}}
  .sidebar.open{{transform:none}}
  .menu-toggle{{display:grid;place-items:center}}
  .progress{{left:0}}
  .cover{{padding-top:66px}}
}}
@media print{{
  .sidebar,.menu-toggle,.to-top,.progress,.copy-btn{{display:none !important}}
  .content{{margin:0;padding:0;max-width:none}}
  .chapter,.cover{{max-width:none;padding-top:24px}}
  .chapter h2,.chapter h3{{break-after:avoid}}
  a{{color:inherit;border:0 !important}}
  pre{{white-space:pre-wrap;word-break:break-word;box-shadow:none}}
}}
</style>
<script>try{{var t=localStorage.getItem('kthw-theme');if(t)document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}</script>
</head>
<body>
<div class="progress" id="progress"><span id="progressBar"></span></div>
<button class="menu-toggle" id="menuToggle" aria-label="打开目录"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>

<aside class="sidebar" id="sidebar">
  <div class="brand">
    <div class="brand-mark">K8s</div>
    <div>
      <div class="brand-title">Kubernetes The Hard Way</div>
      <div class="brand-sub">中文版 · 自包含单文件</div>
    </div>
  </div>
  <div class="theme-bar">
    <label for="theme">主题</label>
    <select id="theme">{theme_options}</select>
  </div>
  <input id="filter" class="filter" type="search" placeholder="过滤目录…" aria-label="过滤目录">
  <nav class="toc" id="toc">
    {toc}
  </nav>
  <div class="sidebar-foot">
    生成自 <code>docs/zh</code> @ <code>{commit}</code><br>
    <a href="{repo}" target="_blank" rel="noopener">github.com/wafbys/iced-kubernetes-the-hard-way</a>
  </div>
</aside>

<main class="content" id="content">
<section id="cover" class="cover">
  <div class="eyebrow">Kubernetes The Hard Way · 中文单文件版</div>
  <h1>Kubernetes The Hard Way</h1>
  <p class="lede">从零手把手搭建一个 Kubernetes 集群的经典教程中文版。本页把 <code>docs/zh/</code> 下
  00–13 章与术语表合并为一个自包含 HTML，可离线阅读。</p>
  <dl class="meta-grid">
    <div class="meta-card"><dt>上游项目</dt><dd><a href="https://github.com/kelseyhightower/kubernetes-the-hard-way" target="_blank" rel="noopener">kelseyhightower/kubernetes-the-hard-way</a></dd></div>
    <div class="meta-card"><dt>上游基线</dt><dd>提交 <code>52eb26d</code>（2025-04-09）</dd></div>
    <div class="meta-card"><dt>组件版本</dt><dd>kubernetes v1.32.x · containerd v2.1.x · cni v1.6.x · etcd v3.6.x</dd></div>
    <div class="meta-card"><dt>本仓库</dt><dd><a href="{repo}" target="_blank" rel="noopener">wafbys/iced-kubernetes-the-hard-way</a></dd></div>
    <div class="meta-card"><dt>内容来源</dt><dd>docs/zh 章节 00–13（含本地补充的 00）＋ reference/glossary</dd></div>
    <div class="meta-card"><dt>生成版本</dt><dd>commit <code>{commit}</code></dd></div>
  </dl>
  <div class="callout">
    <strong>许可与署名：</strong>教程正文源自 Kelsey Hightower 的 <em>Kubernetes The Hard Way</em>。
    中文译文与本地补充内容按 <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="noopener">CC BY-NC-SA 4.0</a> 发布
    （署名 + 非商业 + 相同方式共享）；命令、配置与代码片段按
    <a href="https://www.apache.org/licenses/LICENSE-2.0" target="_blank" rel="noopener">Apache-2.0</a> 授权。仅供个人学习，非生产用途。
  </div>
  <div class="callout">
    <strong>阅读提示：</strong>左侧可切换风格（Anthropic / OpenAI / Google / Microsoft / Apple / GitHub / Stripe / Vercel），
    目录支持关键字过滤并随滚动高亮；代码块悬停右上角可一键复制；右下角按钮返回顶部；打印时自动隐藏导航。
  </div>
</section>

{content}

<footer class="page-foot">
  本页由 <code>docs/zh/</code> 与 <code>reference/glossary.md</code> 自动生成，生成版本 <code>{commit}</code>。<br>
  上游原文：<a href="https://github.com/kelseyhightower/kubernetes-the-hard-way" target="_blank" rel="noopener">kelseyhightower/kubernetes-the-hard-way</a> ·
  本仓库：<a href="{repo}" target="_blank" rel="noopener">wafbys/iced-kubernetes-the-hard-way</a><br>
  许可：文档 CC BY-NC-SA 4.0 ｜ 代码 Apache-2.0。
</footer>
</main>

<button class="to-top" id="toTop" aria-label="返回顶部">↑</button>

<script>
(function () {{
  var sidebar = document.getElementById('sidebar');
  var toggle = document.getElementById('menuToggle');
  toggle.addEventListener('click', function () {{ sidebar.classList.toggle('open'); }});
  sidebar.addEventListener('click', function (e) {{
    if (e.target.closest('a') && window.innerWidth <= 1000) sidebar.classList.remove('open');
  }});

  var themeSel = document.getElementById('theme');
  function applyTheme(t) {{
    if (!t) return;
    document.documentElement.setAttribute('data-theme', t);
    if (themeSel) themeSel.value = t;
  }}
  var savedTheme = null;
  try {{ savedTheme = localStorage.getItem('kthw-theme'); }} catch (e) {{}}
  applyTheme(savedTheme || 'anthropic');
  if (themeSel) {{
    themeSel.addEventListener('change', function () {{
      applyTheme(themeSel.value);
      try {{ localStorage.setItem('kthw-theme', themeSel.value); }} catch (e) {{}}
    }});
  }}

  var bar = document.getElementById('progressBar');
  var toTop = document.getElementById('toTop');
  var links = [].slice.call(document.querySelectorAll('#toc a[href^="#"]'));
  var map = {{}};
  links.forEach(function (a) {{ map[decodeURIComponent(a.getAttribute('href').slice(1))] = a; }});
  var targets = [].slice.call(document.querySelectorAll('.content section[id], .content h2[id], .content h3[id]'));
  var active = null;

  function spy() {{
    var y = (window.scrollY || document.documentElement.scrollTop) + 130;
    var current = null;
    for (var i = 0; i < targets.length; i++) {{
      if (targets[i].offsetTop <= y) current = targets[i]; else break;
    }}
    if (!current) return;
    var a = map[current.id];
    if (!a) return;
    if (a !== active) {{
      if (active) active.classList.remove('active');
      a.classList.add('active');
      active = a;
      if (a.offsetTop < sidebar.scrollTop + 30 || a.offsetTop > sidebar.scrollTop + sidebar.clientHeight - 40) {{
        sidebar.scrollTop = Math.max(0, a.offsetTop - sidebar.clientHeight / 2);
      }}
    }}
  }}

  function onScroll() {{
    var el = document.documentElement;
    var max = el.scrollHeight - el.clientHeight;
    var y = window.scrollY || el.scrollTop;
    bar.style.width = (max > 0 ? (y / max * 100) : 0) + '%';
    toTop.classList.toggle('show', y > 700);
    spy();
  }}
  window.addEventListener('scroll', onScroll, {{ passive: true }});
  window.addEventListener('resize', onScroll);
  onScroll();

  toTop.addEventListener('click', function () {{ window.scrollTo({{ top: 0, behavior: 'smooth' }}); }});

  document.querySelectorAll('.chapter pre').forEach(function (pre) {{
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'copy-btn';
    btn.textContent = '复制';
    btn.addEventListener('click', function () {{
      var code = pre.querySelector('code');
      var text = code ? code.innerText : pre.innerText;
      navigator.clipboard.writeText(text).then(function () {{
        btn.textContent = '已复制';
        setTimeout(function () {{ btn.textContent = '复制'; }}, 1400);
      }}, function () {{ btn.textContent = '复制失败'; }});
    }});
    pre.appendChild(btn);
  }});

  var filter = document.getElementById('filter');
  filter.addEventListener('input', function () {{
    var q = filter.value.trim().toLowerCase();
    document.querySelectorAll('#toc .toc-group').forEach(function (g) {{
      var as = [].slice.call(g.querySelectorAll('a'));
      var chapter = as[0];
      var chapterHit = !q || chapter.textContent.toLowerCase().indexOf(q) >= 0;
      var subHits = 0;
      as.slice(1).forEach(function (a) {{
        var hit = !q || a.textContent.toLowerCase().indexOf(q) >= 0;
        a.classList.toggle('toc-hidden', !hit);
        if (hit) subHits++;
      }});
      var show = chapterHit || subHits > 0;
      chapter.classList.toggle('toc-hidden', !show);
      g.classList.toggle('toc-hidden', !show);
    }});
  }});
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
