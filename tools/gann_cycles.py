#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الدورات — مقيسةً بالحساب الفلكى نفسه، لا منقولةً عن كتاب.

ثلاثة أسئلة، وكلها تُحسم بأرقام:

  ١) ما طول اقتران المشترى والمريخ **فى الإطار المركزى الشمسى**؟ والفرض القائل
     إنه «حوالى 20 سنة» يُختبر مباشرةً.

  ٢) فإن لم يكن 20، فهل هناك بنية 20 سنة على أى حال؟ (نبضة تسعة اقترانات،
     ومقارنتها بالمشترى‑زحل.)

  ٣) وفى أثناء الدورة الكبرى: كم دورة للكواكب الصغيرة تدخل فيها؟ — لأن هذا هو
     معنى «دورات داخل دورة».

ووحدة الحساب **يوم أرضى**، كما طُلب: كل الأطوال تُعرض بالأيام أولًا.

الاستعمال:
    python3 tools/gann_cycles.py
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from astro_conjunctions import R2D, date_to_jd, longitude  # noqa: E402

# متوسطات مدارية (أيام) — المصدر: عناصر كبلرية مستعملة فى astro_conjunctions
PERIOD_D = {
    "mercury": 87.9691, "venus": 224.7008, "earth": 365.2564,
    "mars": 686.9800, "jupiter": 4332.589, "saturn": 10759.22,
}
SUN_DAY = 365.25


def years(days):
    return days / SUN_DAY


def synodic(a, b):
    """دورة الاقتران (أيام) = مقلوب فرق الترددين."""
    return 1.0 / abs(1.0 / PERIOD_D[a] - 1.0 / PERIOD_D[b])


def helio_long(body, jd):
    return longitude(body, jd, "helio") * R2D


def conjunctions(a, b, y0, y1, step=2.0):
    """تواريخ الاقتران المركزى الشمسى بين جرمان (تساوى الطول السماوى)."""
    out, prev, t = [], None, date_to_jd(y0, 1, 1)
    end = date_to_jd(y1, 1, 1)
    while t < end:
        d = (helio_long(a, t) - helio_long(b, t)) % 360.0
        d = d - 360.0 if d > 180.0 else d
        if prev is not None and prev[1] * d < 0 and abs(d - prev[1]) < 90:
            lo, hi = prev[0], t
            for _ in range(40):
                mid = (lo + hi) / 2
                dm = (helio_long(a, mid) - helio_long(b, mid)) % 360.0
                dm = dm - 360.0 if dm > 180.0 else dm
                lo, hi = (mid, hi) if dm * prev[1] > 0 else (lo, mid)
            out.append((lo + hi) / 2)
        prev, t = (t, d), t + step
    return out


def main():
    print("=" * 76)
    print("  ١) أطوال الاقتران — محسوبة، لا مفترضة")
    print("=" * 76)
    pairs = [("mars", "jupiter"), ("jupiter", "saturn"), ("mars", "saturn"),
             ("venus", "jupiter"), ("mercury", "jupiter")]
    measured = {}
    for a, b in pairs:
        C = conjunctions(a, b, 1900, 2030)
        gaps = [(y - x) for x, y in zip(C, C[1:])]
        m = sum(gaps) / len(gaps)
        measured[(a, b)] = m
        print(f"  {a:8}↔{b:8}  {len(C):3} اقترانًا 1900–2030 · "
              f"متوسط {m:8.1f} يومًا = {years(m):6.3f} سنة "
              f"(نظرى {synodic(a, b):8.1f} يومًا)")

    jm = measured[("mars", "jupiter")]
    js = measured[("jupiter", "saturn")]
    print(f"\n  ⇒ المريخ‑المشترى **ليس** دورة 20 سنة: {years(jm):.3f} سنة.")
    print(f"  ⇒ والذى يقارب العشرين هو المشترى‑زحل: {years(js):.3f} سنة.")

    print("\n" + "=" * 76)
    print("  ٢) فهل للعشرين وجود؟ — نبضة التسعة")
    print("=" * 76)
    print(f"  9 × المريخ‑المشترى = {9 * years(jm):.3f} سنة = {9 * jm:.0f} يومًا")
    print(f"  المشترى‑زحل        = {years(js):.3f} سنة")
    print(f"  الفرق {100 * (9 * years(jm) / years(js) - 1):+.2f}%")
    adv = 360.0 / PERIOD_D["jupiter"] * jm
    print(f"\n  وانزلاق موضع الاقتران لكل مرة: المشترى يتقدم {adv:.2f}°")
    print(f"  ⇒ الاقتران يعود إلى نفس البرج كل {360 / adv:.3f} اقتران "
          f"({360 / adv * years(jm):.1f} سنة) — لا كل 9.")
    print(f"  ⇒ فالتسعة ليست عودةً للبرج، بل **نبضة** تقارب طول المشترى‑زحل.")

    print("\n" + "=" * 76)
    print("  ٣) ما يجرى داخل العشرين — التداخل")
    print("=" * 76)
    T = 9 * years(jm)
    print(f"  الدورة الكبرى المفترضة: {T:.2f} سنة = {T * SUN_DAY:.0f} يومًا\n")
    rows = [
        ("عطارد — مدارى", PERIOD_D["mercury"]),
        ("عطارد — سينودى (من الأرض)", synodic("mercury", "earth")),
        ("عطارد — سينودى (من المريخ)", synodic("mercury", "mars")),
        ("الزهرة — مدارى", PERIOD_D["venus"]),
        ("الزهرة — سينودى (من الأرض)", synodic("venus", "earth")),
        ("الزهرة — سينودى (من المريخ)", synodic("venus", "mars")),
        ("المريخ — مدارى", PERIOD_D["mars"]),
        ("المريخ‑المشترى — اقتران", jm),
        ("المشترى — مدارى", PERIOD_D["jupiter"]),
        ("زحل — مدارى", PERIOD_D["saturn"]),
    ]
    for name, p in rows:
        n = T * SUN_DAY / p
        print(f"    {name:28} {p:9.1f} ي · {n:6.2f} دورة داخل العشرين")

    print("\n  والملاحظة: الزهرة‑المريخ تعطى **22.0** بالضبط — أول عدد صحيح")
    print("  يقع على دورة كاملة داخل النافذة. وعطارد‑الأرض 63.4 ≈ 7×9.")
    print("  فالتداخل موجود حسابيًّا؛ والسؤال هل يوافق السوق (وقد اختُبر: لا، §14.10).")


if __name__ == "__main__":
    main()
