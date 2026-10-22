#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
السرعة الهليوسنتريكية والقانون الطبيعى بين 0 و1.

السؤال الأول: كم درجة يقطع كل كوكب فى اليوم **حول الشمس**؟
السؤال الثالث: إذا تحرّك السعر بسرعة 1 مقابل 1 تقابل مع الزمن فى المنتصف،
وإذا كان أبطأ تقابل عند كسر ثابت — الثمن والربع — فما صيغة ذلك، وهل السوق به؟

والبناء الرياضى (لا النقل):

    سعر يبدأ من 0 ويتحرك بسرعة v درجة/يوم، وزمن يبدأ من 360 ويتحرك بسرعة
    1 درجة/يوم نحو الآخر — يلتقيان حيث:

        v·t + t = 360      ⇒      t = 360/(1+v)      ⇒      θ_سعر = 360·v/(1+v)

    فالكسر من المدى:

        f = v/(1+v)          ⟺          v = f/(1−f)

    و f = 1/2  ⟺  v = 1  — وهو «المنتصف» حين تتساوى السرعتان.

    ولو كان v = 1/T (T بالسنوات ذات الـ360 يومًا):

        f = 1/(1+T)

    والتناظر:  f(T) + f(1/T) = 1 — فالدورة وتربيعها يلتقيان عند كسرين متتامّين.

وفيه يظهر الجواب: الكسور «الطبيعية» ليست مفروضة، بل ناتجة عن **أعداد صحيحة**:
الثمن هو T=7، والربع T=3، والثلث T=2، والمنتصف T=1، والثلاثان T=1/2.

التشغيل:
    python3 tools/heliocentric_law.py
    python3 tools/heliocentric_law.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv
import math
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import astro_conjunctions as A  # noqa: E402

NAT = [(1 / 8, "1/8"), (1 / 4, "1/4"), (1 / 3, "1/3"), (3 / 8, "3/8"),
       (1 / 2, "1/2"), (5 / 8, "5/8"), (2 / 3, "2/3"), (3 / 4, "3/4"), (7 / 8, "7/8")]
ARABIC = {"mercury": "عطارد", "venus": "الزهرة", "earth": "الأرض", "mars": "المريخ",
          "jupiter": "المشترى", "saturn": "زحل", "uranus": "أورانوس", "neptune": "نبتون"}


def speeds():
    out = []
    for name in ("mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"):
        base, rate = A.ELEMENTS[name]
        v = rate[3] / 36525.0            # درجة/يوم
        out.append(dict(name=name, v=v, vy=v * 365.25, T=360.0 / v / 365.25,
                        f=v / (1 + v)))
    return out


def report_speeds():
    print("=" * 84)
    print("١ — كم درجة يقطع كل كوكب فى اليوم (هليوسنتريك)")
    print("=" * 84)
    print("\nالسرعة = معدّل الطول الوسطى لكل قرن ÷ 36525. (نفس عناصر `astro_conjunctions`.)\n")
    print(f"{'الكوكب':<10}{'°/يوم':>10}{'°/سنة':>11}{'سنة مدارية':>12}{'f=v/(1+v)':>12}")
    rows = speeds()
    for s in rows:
        print(f"{ARABIC[s['name']]:<10}{s['v']:>10.4f}{s['vy']:>11.2f}{s['T']:>12.3f}{s['f']:>12.4f}")
    print("\nوالأرض هى الشمس مركزًا أرضيًّا: 0.9856°/يوم — أى أن «يوم = درجة» هو")
    print("سرعة الشمس مقرَّبة. فحين نقول 1:1 فإننا نقول: **الشمس**.")
    return rows


def report_derivation():
    print("\n" + "=" * 84)
    print("٢ — الاشتقاق: من أين جاءت الثمن والربع")
    print("=" * 84)
    print("""
    سعر من 0 بسرعة v، وزمن من 360 بسرعة 1، يلتقيان عند:

        v·t + t = 360     ⇒     f = v/(1+v)

    فالكسر ليس اختيارًا: هو **نتيجة قسمة سرعتين**.
""")
    print(f"{'f':>7}{'v=f/(1−f)':>12}{'T=1/v':>9}{'اقرأها كـ':>26}")
    for f, name in NAT:
        v = f / (1 - f)
        T = 1 / v
        note = ("دورة = 7" if abs(T - 7) < 1e-9 else "دورة = 3" if abs(T - 3) < 1e-9 else
                "دورة = 2" if abs(T - 2) < 1e-9 else "دورة = 1 (الشمس)" if abs(T - 1) < 1e-9 else
                "نصف دورة" if abs(T - 0.5) < 1e-9 else "ثلث دورة" if abs(T - 1 / 3) < 1e-9 else
                "سُبع دورة" if abs(T - 1 / 7) < 1e-9 else "")
        print(f"{name:>7}{v:>12.3f}{T:>9.3f}{note:>26}")
    print("\n    والتناظر: f(T) + f(1/T) = 1.")
    for T in (2, 3, 7):
        print(f"      T={T}: f={1/(1+T):.4f}   و  T=1/{T}: f={T/(1+T):.4f}"
              f"   مجموعهما {1/(1+T) + T/(1+T):.3f}")
    print("\n    ⇒ **الأرقام 3 و7 نفسها، مقروءة من الطرف الآخر.** الثُمن دورةٌ من سبع،")
    print("      والربع دورةٌ من ثلاث. ولهذا تظهر 3 و7 فى التقسيم وفى الدورات معًا.")


def report_planets(rows):
    print("\n" + "=" * 84)
    print("٣ — الكواكب على هذا القانون")
    print("=" * 84)
    print(f"\n{'الكوكب':<10}{'v':>9}{'f':>9}{'أقرب كسر':>10}{'خطأ':>9}"
          f"{'1/f − 1':>10}{'= الدورة':>10}")
    for s in rows:
        f = s["f"]
        k = min(NAT, key=lambda x: abs(f - x[0]))
        T = 1 / f - 1
        print(f"{ARABIC[s['name']]:<10}{s['v']:>9.4f}{f:>9.4f}{k[1]:>10}"
              f"{100 * (f - k[0]) / k[0]:>+8.1f}%{T:>10.2f}{s['T']:>10.3f}")
    print("\n    والقراءة: **الشمس 1/2 بالضبط** — أى أن «1:1 ⇒ المنتصف» ليس قاعدة موضوعة،")
    print("    بل السنة الشمسية مقيسةً بوحدة الـ360 يومًا. والمريخ 1/3 لأن سنته سنتان،")
    print("    والمشترى 1/13 لأن سنته 12، وزحل 1/31 لأن سنته 30.")
    print("    ⇒ أرقام 2 و12 و30 التى بُنى عليها الكتاب هى نفسها مقامات الكسور.")
    print("    والعمود الأخيران متساويان — والمساواة **متطابقة**، لا مصادفة:"
          "\n      1/f − 1 = (1+v)/v − 1 = 1/v = الدورة بوحدات 360 يومًا.")


def load(path, min_rows):
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


def zigzag(px, th=0.20, skip=30):
    p = px[skip:]
    if len(p) < 10:
        return []
    out, trend = [], 0
    hi = lo = p[0]
    hii = loi = 0
    for i, x in enumerate(p):
        if trend >= 0:
            if x > hi:
                hi, hii = x, i
            elif x <= hi * (1 - th):
                if trend > 0 or not out:
                    out.append(hii + skip)
                trend, lo, loi = -1, x, i
        if trend <= 0:
            if x < lo:
                lo, loi = x, i
            elif x >= lo * (1 + th):
                if trend < 0:
                    out.append(loi + skip)
                trend, hi, hii = 1, x, i
    return out


def report_market(path, min_rows):
    data = load(path, min_rows)
    print("\n" + "=" * 84)
    print("٤ — وسرعة السهم هى v")
    print("=" * 84)
    print("\nφ = 360·log₁₀ P (الدرجة الوحيدة الثابتة بنقل العلامة — §14.9)،")
    print("و v = |Δφ| بين انعطافين ÷ الأيام. وحدةٌ واحدة مع الكواكب: درجة/يوم.\n")
    per, allv = [], []
    for t, v in data.items():
        ds = list(v)
        px = np.array([v[d] for d in ds], float)
        phi = 360 * np.log10(px)
        idx = zigzag(px)
        sp = [abs(phi[b] - phi[a]) / (b - a) for a, b in zip(idx, idx[1:]) if b > a]
        if sp:
            per.append(np.median(sp))
            allv.extend(sp)
    per = np.array(per)
    print(f"{'المئين':>8}{'v':>9}{'f=v/(1+v)':>12}{'أقرب كسر':>11}")
    for q in (10, 25, 50, 75, 90):
        x = float(np.percentile(per, q))
        k = min(NAT, key=lambda z: abs(x / (1 + x) - z[0]))
        print(f"{q:>8}{x:>9.3f}{x / (1 + x):>12.3f}{k[1]:>11}")
    print(f"\n  والشمس v = 0.9856 ⇒ f = 0.4964 (1/2).")
    print(f"  ووسيط السهم v = {np.median(per):.3f} ⇒ f = {np.median(per) / (1 + np.median(per)):.3f}.")
    print("  ⇒ السهم المتوسط **أسرع من الشمس**، فيلقى الزمن عند 5/8 لا عند 1/2.")

    print("\n" + "=" * 84)
    print("٥ — الاختبار: هل الارتدادات تقف عند الكسور؟")
    print("=" * 84)
    rho = []
    for t, v in data.items():
        ds = list(v)
        px = np.array([v[d] for d in ds], float)
        idx = zigzag(px)
        for a, b, c in zip(idx, idx[1:], idx[2:]):
            A_ = abs(px[b] - px[a])
            B_ = abs(px[b] - px[c])
            if A_ > 0:
                rho.append(B_ / A_)
    rho = np.array(rho)
    rho = rho[(rho > 0.02) & (rho < 1.5)]
    print(f"\n{len(rho):,} حركة · وρ = مدى الحركة التالية ÷ مدى السابقة")
    print(f"وسيط ρ = {np.median(rho):.3f}\n")
    print(f"{'الكسر':>7}{'±0.03':>9}{'الجوار ±0.03':>14}{'النسبة':>9}")
    ratios = []
    for x, name in NAT:
        a = int(np.sum(np.abs(rho - x) <= 0.03))
        lo = int(np.sum(np.abs(rho - (x - 0.09)) <= 0.03))
        hi = int(np.sum(np.abs(rho - (x + 0.09)) <= 0.03))
        base = (lo + hi) / 2
        ratios.append(a / base if base else float("nan"))
        print(f"{name:>7}{a:>9}{base:>14.1f}{a / base if base else float('nan'):>9.2f}")
    print(f"\n  متوسط النسب {np.nanmean(ratios):.2f} — والمتوقع بلا تركيز 1.00.")
    print("  ⇒ لا تكدّس عند أى كسر طبيعى: التوزيع أملس، والكسور شبكة مفروضة على متصل.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--min-rows", type=int, default=300)
    ns = ap.parse_args()
    rows = report_speeds()
    report_derivation()
    report_planets(rows)
    if ns.csv:
        report_market(ns.csv, ns.min_rows)


if __name__ == "__main__":
    main()
