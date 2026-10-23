#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بروتوكول الإخفاء — تطويرٌ على نافذة، وتحققٌ على نافذة أُخفيت.

البيانات تُقسم ثلاثًا **قبل** أى حساب:

    O  لم تُحسب قبلًا   1998-01-01 → 2013-12-31   (31 تاريخ إعادة توازن)
    T  تطوير           2014-01-01 → 2018-12-31   (10 تواريخ)
    H  مخفى            2019-01-01 → 2025-10-27   (13 تاريخًا)

والقاعدة: **لا يُختار شىء من H.** تُثبَّت القواعد والأوزان والمدى قبل النظر:

    المصفاة كاملة       أوزان الكتاب (1.5 · 1.0 · 2.0 · 1.5 · 2.0 · 1.0)
    البنية وحدها        1.5 · 1.0
    المحرّك العددى      2.0 · 1.5 · 2.0 · 1.0  (مربع + رقم + زمن + دورة)
    الزخم               عائد 126 يومًا — **مسطرة** لا مرشّح: لبيان ما يبدو عليه
                        الترتيب حين يعمل شىء لا يخص جان
    عشوائى             ضابط

والاختيار الوحيد المسموح: تُختار النسخة الفائزة على T، ثم تُقرأ على H كما هى.
ثم يُجرَّب الأسوأ: **توفيق الأوزان الستة على T** (ألف وزن)، ويُقرأ على H.

القياس: كل 126 يوم تداول، تُرتَّب الأسهم، ويُقارن وسيط العُشر الأعلى بوسيط السوق
فى التاريخ نفسه، ثم يُقاس العائد 126 يومًا. لا شىء يُنبَّأ من المستقبل،
ولا سهم يدخل الترتيب قبل أن يكون له 260 يومًا من تاريخه.

التشغيل:
    python3 tools/holdout.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv
import math
import sys
from datetime import date as _date

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import gann_sieve as S  # noqa: E402

WINDOWS = (("O — لم تُحسب قبلًا", "1998-01-01", "2013-12-31"),
           ("T — تطوير", "2014-01-01", "2018-12-31"),
           ("H — مخفى", "2019-01-01", "2025-10-27"))
MODES = (("full", "المصفاة كاملة"), ("trend", "البنية وحدها"), ("gann", "المحرّك العددى"))
COMPONENTS = ("struct", "pos", "square", "num", "time", "cyc")
COMP_LABEL = {"struct": "البنية", "pos": "الموقع", "square": "المربع",
              "num": "الرقم", "time": "الزمن", "cyc": "الدورة", "mom": "الزخم"}


def load_all(path, min_rows):
    by = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                c = float(r["close"])
            except ValueError:
                continue
            if c > 0:
                by[r["ticker"]][r["date"]] = c
    return {t: dict(sorted(v.items())) for t, v in by.items()
            if not t.upper().startswith("EGX") and len(v) >= min_rows}


def build_panel(data, grid, H):
    """صفوف (تاريخ، سهم، عائد أمامى، الدرجات ومكوّناتها) — تُحسب مرة، تُقرأ منها كل قاعدة."""
    panel = collections.defaultdict(list)
    for rd in grid:
        for t, v in data.items():
            ds = list(v)
            if ds[0] > rd or ds[-1] <= rd:
                continue
            i = max(j for j, d in enumerate(ds) if d <= rd)
            if i < 260 or i + H >= len(ds):
                continue
            px = np.array([v[d] for d in ds], float)
            r = S.score_row(ds, px, i, "full")
            if not r:
                continue
            row = dict(ticker=t, fwd=v[ds[i + H]] / v[ds[i]] - 1,
                       mom=v[ds[i]] / v[ds[i - H]] - 1 if i >= H else np.nan,
                       full=r["total"],
                       trend=S.score_row(ds, px, i, "trend")["total"],
                       gann=S.score_row(ds, px, i, "gann")["total"])
            for c in COMPONENTS:
                row[c] = r["s_" + c]
            panel[rd].append(row)
    return panel


def tstat(x):
    x = np.asarray(x, float)
    if len(x) < 3:
        return 0.0
    s = x.std(ddof=1)
    return x.mean() / (s / math.sqrt(len(x))) if s > 0 else 0.0


def evaluate(panel, dates, key, rng=None):
    """وسيط العُشر الأعلى ناقص وسيط السوق، وناقص العُشر الأدنى."""
    tops, bots = [], []
    for d in dates:
        rows = [r for r in panel[d] if np.isfinite(r.get(key, np.nan))]
        if len(rows) < 30:
            continue
        n = len(rows)
        q = max(3, n // 10)
        order = list(rows)
        if rng is None:
            order.sort(key=lambda r: -r[key])
        else:
            rng.shuffle(order)
        f = [r["fwd"] for r in order]
        med = float(np.median(f))
        tops.append(float(np.median(f[:q])) - med)
        bots.append(float(np.median(f[-q:])) - med)
    if not tops:
        return None
    a, b = np.array(tops), np.array(bots)
    return dict(n=len(a), top=float(a.mean()), t=tstat(a),
                bot=float(b.mean()), pos=float(np.mean(a > b)))


def t_of_weights(w, mats):
    tops = []
    for M, f in mats:
        order = np.argsort(-(M @ w))
        q = max(3, len(f) // 10)
        tops.append(float(np.median(f[order[:q]])) - float(np.median(f)))
    return tstat(tops) if tops else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--min-rows", type=int, default=300)
    ap.add_argument("--shuffles", type=int, default=200)
    ap.add_argument("--fits", type=int, default=1000)
    ap.add_argument("--horizon", type=int, default=126)
    ns = ap.parse_args()

    data = load_all(ns.csv, ns.min_rows)
    cal = sorted({d for v in data.values() for d in v})
    cal = [d for d in cal if d >= "1998-01-01"]
    H = ns.horizon
    grid = cal[::H]
    panel = build_panel(data, grid, H)
    win = {name: [d for d in grid if a <= d <= b] for name, a, b in WINDOWS}

    print("=" * 90)
    print("٠ — التقسيم، قبل أى حساب")
    print("=" * 90)
    print(f"\nأسهم {len(data)} · كل {H} يوم تداول · {len(grid)} تاريخ إعادة توازن"
          f" · عائد أمامى {H} يومًا\n")
    print(f"{'النافذة':<20}{'من':>12}{'إلى':>12}{'تواريخ':>8}{'أسهم/تاريخ':>13}")
    for name, a, b in WINDOWS:
        m = int(np.mean([len(panel[d]) for d in win[name]])) if win[name] else 0
        print(f"{name:<20}{a:>12}{b:>12}{len(win[name]):>8}{m:>13}")

    print("\n" + "=" * 90)
    print("١ — المصفوفة كاملة: كل قاعدة على كل نافذة (لا اختيار)")
    print("=" * 90)
    print(f"\n{'القاعدة':<18}" + "".join(f"{n:<23}" for n, _, _ in WINDOWS))
    table = {}
    for key, label in list(MODES) + [("mom", "الزخم")]:
        line = f"{label:<18}"
        for name, _, _ in WINDOWS:
            s = evaluate(panel, win[name], key)
            table[(key, name)] = s
            line += (f"{100 * s['top']:+6.2f}% (t={s['t']:+5.2f})" if s else "—").ljust(23)
        print(line)
    rng = np.random.default_rng(21)
    line = f"{'عشوائى':<18}"
    for name, _, _ in WINDOWS:
        vals = [evaluate(panel, win[name], "fwd", rng)["top"] for _ in range(ns.shuffles)]
        line += f"{100 * np.mean(vals):+6.2f}% (±{100 * np.std(vals):4.2f})".ljust(23)
    print(line)
    print("\n(عمود الزخم مسطرة لا مرشّح: لا علاقة له بجان، ويُقرأ كسقف لما يمكن أن يفعله ترتيب بسيط.)")

    print("\n" + "=" * 90)
    print("٢ — الاختيار على T ثم القراءة على H")
    print("=" * 90)
    best = max(MODES, key=lambda m: table[(m[0], "T — تطوير")]["t"])
    print(f"\nالفائزة على التطوير: **{best[1]}** — t = {table[(best[0], 'T — تطوير')]['t']:+.2f}\n")
    for name, _, _ in WINDOWS:
        s = table[(best[0], name)]
        print(f"    {name:<20} أعلى−السوق {100 * s['top']:+6.2f}%  ·  t = {s['t']:+5.2f}"
              f"  ·  أعلى>أدنى فى {100 * s['pos']:.0f}% من التواريخ")
    d0, d1 = table[(best[0], "T — تطوير")]["t"], table[(best[0], "H — مخفى")]["t"]
    print(f"\n    T {d0:+.2f}  →  H {d1:+.2f}   (تغيّر {d1 - d0:+.2f})")
    print(f"    وللمقارنة: نفس القاعدة على O {table[(best[0], 'O — لم تُحسب قبلًا')]['t']:+.2f}")

    print("\n" + "=" * 90)
    print(f"٣ — التوفيق على T: {ns.fits} وزنًا — ماذا يفعل الأفضل منها على H؟")
    print("=" * 90)
    def sample_dates(name, cap=40):
        ds = [d for d in win[name] if len(panel[d]) >= 30]
        if len(ds) > cap:
            idx = np.linspace(0, len(ds) - 1, cap).round().astype(int)
            ds = [ds[i] for i in sorted(set(idx))]
        return ds

    mats = {name: [(np.array([[r[c] for c in COMPONENTS] for r in panel[d]]),
                    np.array([r["fwd"] for r in panel[d]]))
                   for d in sample_dates(name)] for name, _, _ in WINDOWS}
    rng = np.random.default_rng(77)
    Wt = rng.dirichlet(np.ones(len(COMPONENTS)), size=ns.fits)
    tT = np.array([t_of_weights(w, mats["T — تطوير"]) for w in Wt])
    tH = np.array([t_of_weights(w, mats["H — مخفى"]) for w in Wt])
    tO = np.array([t_of_weights(w, mats["O — لم تُحسب قبلًا"]) for w in Wt])
    k = int(np.argmax(tT))
    print(f"\n{len(Wt)} وزنًا · T {len(mats['T — تطوير'])} تواريخ · H {len(mats['H — مخفى'])}\n")
    print(f"  توزيع t على T: وسيط {np.median(tT):+.2f} · أفضل {tT.max():+.2f} · أسوأ {tT.min():+.2f}")
    print(f"  توزيع t على H: وسيط {np.median(tH):+.2f} · أفضل {tH.max():+.2f} · أسوأ {tH.min():+.2f}")
    print(f"\n  ارتباط t(T) بـ t(H) عبر الأوزان: **{np.corrcoef(tT, tH)[0, 1]:+.2f}**")
    print(f"  ارتباط t(H) بـ t(O) عبر الأوزان: {np.corrcoef(tH, tO)[0, 1]:+.2f}")
    print(f"\n  أفضل وزن على T: t = {tT[k]:+.2f}")
    print(f"    على H: {tH[k]:+.2f}  (فارق {tH[k] - tT[k]:+.2f})")
    print(f"    على O: {tO[k]:+.2f}")
    print(f"    ومرتبته فى H: {100 * float(np.mean(tH < tH[k])):.0f}%")
    print(f"\n  ⇒ توفيق على {len(mats['T — تطوير'])} تواريخ يبلغ t = {tT.max():+.2f}،"
          f" ثم يعود على المخفى إلى {tH[k]:+.2f}.")

    print("\n" + "=" * 90)
    print("٤ — المكوّنات الستة وحدها: أيّها يحمل إشارة ثابتة؟")
    print("=" * 90)
    print(f"\n{'المكوّن':<12}" + "".join(f"{n[:12]:>20}" for n, _, _ in WINDOWS))
    comp = {}
    for key in list(COMPONENTS) + ["mom"]:
        line = f"{COMP_LABEL[key]:<12}"
        for name, _, _ in WINDOWS:
            s = evaluate(panel, win[name], key)
            comp[(key, name)] = s
            line += f"{100 * s['top']:+6.2f}% (t={s['t']:+5.2f})".rjust(20)
        print(line)
    stable = [k for k in COMPONENTS
              if len({np.sign(comp[(k, n)]["t"]) for n in win}) == 1]
    print(f"\n  المكوّنات التى أخذت الإشارة نفسها فى النوافذ الثلاث: "
          f"{' · '.join(COMP_LABEL[k] for k in stable) or 'لا شىء'}")
    for k in stable:
        print(f"    {COMP_LABEL[k]}: " + " · ".join(
            f"{n[:1]} {comp[(k, n)]['t']:+.2f}" for n in win))
    print("\n  ولا يُبنى على واحد منها: ستة مكوّنات × ثلاث نوافذ = ثمانى عشرة مقارنة.")

    print("\n" + "=" * 90)
    print("٥ — محفظة: عشر أسهم تُشترى مرة وتُترك — والعائد كله من الجزء المخفى")
    print("=" * 90)
    last = max(d for v in data.values() for d in v)
    edge = _date(*map(int, last.split("-"))).toordinal() - 7
    for start in ("2019-01-02", "2021-01-03", "2023-01-02"):
        rows = []
        for t, v in data.items():
            ds = list(v)
            if ds[0] > start or ds[-1] <= start:
                continue
            if _date(*map(int, ds[-1].split("-"))).toordinal() < edge:
                continue                      # خرج من التداول قبل النهاية
            i = max(j for j, d in enumerate(ds) if d <= start)
            if i < 260:
                continue
            r = S.score_row(ds, np.array([v[d] for d in ds], float), i, "full")
            if not r:
                continue
            rows.append(dict(ticker=t, score=r["total"], ret=v[ds[-1]] / v[ds[i]] - 1))
        if len(rows) < 40:
            continue
        rows.sort(key=lambda r: -r["score"])
        top = rows[:10]
        allr = np.array([r["ret"] for r in rows])
        top_r = float(np.mean([r["ret"] for r in top]))
        rng = np.random.default_rng(33)
        draw = [np.mean(rng.choice(allr, 10, replace=False)) for _ in range(2000)]
        print(f"\n  شراء {start} → {last}  ({len(rows)} سهمًا)")
        print(f"    المحفظة {100 * top_r:+7.1f}%  |  وسيط السهم {100 * np.median(allr):+7.1f}%"
              f"  |  المتوسط {100 * allr.mean():+7.1f}%")
        print(f"    مرتبتها بين 2000 محفظة عشوائية: {100 * float(np.mean(np.array(draw) < top_r)):.0f}%")
        print(f"    أسهمها: {' · '.join(r['ticker'] for r in top)}")

    counts = " · ".join(str(len(win[n])) for n, _, _ in WINDOWS)
    print("\n" + "=" * 90)
    print("٦ — حدود الاختبار")
    print("=" * 90)
    for line in (
        "• الأرشيف أسهم مُدرجة اليوم: من خرج من السوق غائب ⇒ تحيّز بقاء، لا يُصلح بلا ملف شطب.",
        "• الإغلاق غير معدَّل بتجزئة ⇒ العائد يحمل أثر التجزئة (ملف الإجراءات مفقود — §5.3 من `02`).",
        f"• سوق واحد وعملة واحدة؛ والتواريخ {counts}، فـ t = 2 عند 13 تاريخًا ليس t = 2 عند 300.",
        "• إفصاح: اختبار §18.7 السابق جمع 2014–2025 كاملًا، فمرّ على H قبل هذا الفصل ولا يمحو ذلك.",
        "  ولذلك يُعرض كل شىء هنا، ولا يُختار إلا ما اختاره T.",
    ):
        print(line)


if __name__ == "__main__":
    main()
