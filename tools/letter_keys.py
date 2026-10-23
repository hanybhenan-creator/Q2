#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مفاتيح التحويل فى خطابى جان — استنفادٌ قبل أى «تصحيح» للمصدر.

سبب وجود هذا الملف: أعلنتُ فى §23 من `04` «خطأين مطبعيين» عند جان،
ثم تبيّن أن المفتاح الصحيح منصوصٌ فى الصفحة نفسها، وأن خطأى كان فى قراءتى.

فالقاعدة التى يُنفّذها:

    لا يُقال «خطأ فى المصدر» حتى تُجرَّب **كل** المقاييس المنصوصة فيه،
    ويُثبت أن أىًّا منها لا يُنتج الرقم.

والخطابان يعطيان مفاتيحهما صراحةً:

    الصويا   «one hour of Time equals 15 degrees … we use one cent of Price»
             ⇒ 1 سنت = 15°  ·  24 سنتًا = 360°
    البنّ     أربعة مقاييس معلنة للسعر 8729:
             1 نقطة · 30 نقطة · 12 نقطة («مقياس المشترى») · 1 دولار

فالملف يُجرّبها كلها على كل سطر، ويطبع المفتاح الموافق. وحين يوافق مفتاحٌ
منصوص كلَّ الأسطر، لا يبقى موضعٌ لـ«خطأ مطبعى».

التشغيل:
    python3 tools/letter_keys.py
"""

import sys

SIGNS = ("الحمل", "الثور", "الجوزاء", "السرطان", "الأسد", "العذراء",
         "الميزان", "العقرب", "القوس", "الجدي", "الدلو", "الحوت")


def sign(deg):
    d = deg % 360.0
    return f"{int(d % 30)}°{int((d % 30 % 1) * 60):02d}' {SIGNS[int(d // 30)]}"


#  ─────────────────────────────────────────────────────────────────────
#  أسطر الخطابين كما كُتبت (السعر، ما قاله جان)
#  ─────────────────────────────────────────────────────────────────────

SOY = [
    (300.0,   180.0, "30 degrees Virgo"),
    (302.0,   210.0, "30 degrees Libra"),
    (304.0,   240.0, "30 degrees Scorpio"),
    (311.25,  348.75, "18 degrees 45' Pisces"),
    (308.5,   307.5,  "square (90°) to Saturn"),
]

COFFEE = [
    (8729.0,  89.0,  "29° Gemini"),
    (8729.0,  290.97, "21° Capricorn"),
    (8729.0,  7.5,   "7° 30' Aries"),
    (8729.0,  87.29, "27° 16' Gemini"),
]

#  المفاتيح المعلنة: (الاسم، الدالة من السعر إلى الدرجة، أى خطاب)
KEYS = [
    ("1 نقطة = 1°",        lambda p: p,                      "coffee"),
    ("30 نقطة = 1°",       lambda p: p / 30.0,               "coffee"),
    ("12 نقطة = 1°",       lambda p: p / 12.0,               "coffee"),
    ("1 دولار = 1°",       lambda p: p / 100.0,              "coffee"),
    ("1 سنت = 1°",         lambda p: p,                      "soy"),
    ("1 سنت = 15°",        lambda p: p * 15.0,               "soy"),
    ("1 سنت = 15° (+45° ربع)", lambda p: p * 15.0 + 45.0,    "soy"),
]


def run(rows, tag, per_line=False):
    """per_line=True: المفاتيح بدائل للخط نفسه (البنّ) · False: مفتاح واحد للخطاب كله (الصويا)."""
    print("=" * 84)
    print(f"{tag}: {len(rows)} سطرًا · {len(KEYS)} مفتاحًا معلنًا")
    print("=" * 84)
    print(f"\n{'السعر':>10}{'المطلوب':>10}{'نصّ جان':>26}")
    for p, want, claim in rows:
        print(f"{p:>10.3f}{want:>10.2f}{claim:>26}")

    if per_line:
        print(f"\n{'السطر':<28}{'المفتاح المطابق':<26}{'الفرق':>8}")
        covered = 0
        for p, want, claim in rows:
            best = None
            for name, fn, _ in KEYS:
                d = (fn(p) % 360.0 - want) % 360.0
                d = min(d, 360.0 - d)
                if best is None or d < best[1]:
                    best = (name, d)
            covered += best[1] <= 0.5
            print(f"{claim:<28}{best[0]:<26}{best[1]:>7.2f}°")
        print(f"\n  ⇒ {covered}/{len(rows)} سطرًا يُنتجه مفتاحٌ معلن. "
              f"{'ولا موضع لخطأ مطبعى.' if covered == len(rows) else 'ويُبحث فى الباقى.'}")
        return (f"{covered}/{len(rows)} بمفاتيح معلنة", 0.0) if covered else None

    print(f"\n{'المفتاح':<26}{'يطابق':>8}{'أقصى فرق':>11}{'الحكم':>18}")
    best = None
    for name, fn, _ in KEYS:
        diffs = []
        for p, want, _ in rows:
            d = (fn(p) % 360.0 - want) % 360.0
            d = min(d, 360.0 - d)
            diffs.append(d)
        hit = sum(1 for d in diffs if d <= 0.5)
        worst = max(diffs)
        verdict = "✔ كل الأسطر" if hit == len(rows) else (f"{hit}/{len(rows)}" if hit else "✘ لا شىء")
        print(f"{name:<26}{hit:>5}/{len(rows)}{worst:>10.2f}°{verdict:>18}")
        if hit == len(rows) and (best is None or worst < best[1]):
            best = (name, worst)

    print()
    if best:
        print(f"  ⇒ المفتاح المنصوص **{best[0]}** يطابق كل الأسطر (أقصى فرق {best[1]:.2f}°).")
        print("     فلا موضع لخطأ مطبعى فى هذه السطور، ولا لتصحيح.")
    else:
        print("  ⇒ لا مفتاح واحد يغطّى كل الأسطر — يُجرَّب لكل سطر على حدة.")
    return best


def main():
    print(__doc__)
    soy = run(SOY, "خطاب الصويا — 2 ديسمبر 1953")
    coffee = run(COFFEE, "خطاب البنّ — 19 مارس 1954", per_line=True)
    print("=" * 84)
    print("الخلاصة")
    print("=" * 84)
    print(f"\n  الصويا: مفتاحٌ واحد معلن يغطّى الكل — {soy[0] if soy else '—'}")
    print(f"  البنّ  : ألفاظه أربعة لكل سعر واحد — {coffee[0] if coffee else '—'}")
    print("""
  والدرس المسجَّل فى docs/07-corrections.md:

    ادّعيتُ خطأين مطبعيين عند جان. ولم يكن ثمّة خطأ.
    311.25 × 15 = 4,668.75 ≡ 348.75 = 18°45' الحوت — كما كتبه حرفًا.
    8,729 / 100 = 87.29 ≡ 27°17' الجوزاء — ونصّه 27°16'.

  والقاعدة التى يفرضها هذا الملف: لا يُنسب خطأ إلى مصدر قبل استنفاد
  كل مفتاح ينصّ عليه هو نفسه.
""")


if __name__ == "__main__":
    main()
