#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مقياس كل كوكب — هل التحويل قسمة، وهل المقياس اختيارى؟

السؤال: كيف يُحوَّل السعر إلى درجة تُقارن بكوكب؟ وما مقياس كل كوكب؟

والجواب المكتوب فى خطاب البنّ (19 مارس 1954)، أربعة مقاييس للسعر 8729:

    «بمقياس نقطة لكل درجة، 8729 تساوى 29° الجوزاء.
     وبمقياس 30 نقطة لكل درجة، تساوى 21° الجدى.
     وبمقياس المشترى 12 نقطة لكل درجة، تساوى 7° 30' الحمل.
     وبمقياس السنت لكل درجة، تساوى 27° 6' الجوزاء.»

  ⇒ التحويل **قسمة**:  θ = P / s       (s: نقاط لكل درجة)

  وهو نفس ما فى `mikula_price_longitude` بالفصل الثامن، ونفس ما فى §19.

والقانون الذى يجعل المقاييس غير اختيارية:

    السرعة الزاوية للكوكب  v  (درجة/يوم)
    ⇒ المقياس الطبيعى        s = 1/v          (نقاط لكل درجة)
    ⇒ وهو نفسه             s = الدورة ÷ 360 يومًا

    الشمس   1.015 ≈ 1     المشترى 12.036 ≈ 12     زحل 29.877 ≈ 30

  ⇒ **1 و12 و30 هى عطارد... لا: هى الشمس والمشترى وزحل.** وليست أرقامًا مخترعة.

والنتيجة التى تُغلق الباب — وهى التى تجعل السؤالين سؤالًا واحدًا:

    s × 360 = عدد النقاط فى الدورة الكاملة للكوكب = عدد أيام دورته
    ⇒ 1 نقطة = 1 يوم، **لكل كوكب**، مهما اختلف s

    ودرجة السعر المقطوعة = (P − P₀)/s
    ودرجة الكوكب المقطوعة = (t − t₀)/s
    ⇒ يتساويان إذا وفقط إذا  P − P₀ = t − t₀

  ⇒ «مقياس الكوكب» ليس أداة ثانية: هو **القاعدة نفسها على دائرة أخرى**.

التشغيل:
    python3 tools/planet_scale.py
    python3 tools/planet_scale.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import astro_conjunctions as A  # noqa: E402

AR = {"mercury": "عطارد", "venus": "الزهرة", "earth": "الأرض", "mars": "المريخ",
      "jupiter": "المشترى", "saturn": "زحل", "uranus": "أورانوس", "neptune": "نبتون"}
BODIES = tuple(AR)
GANES = {"earth": 1, "mars": 2, "jupiter": 12, "saturn": 30}

#  خطاب البنّ: القاع 435 (1931-04-16) والقمة 8729 (1954-03-19)
COFFEE_LOW, COFFEE_HIGH = 435.0, 8729.0


def scales():
    out = {}
    for b in BODIES:
        v = A.ELEMENTS[b][1][3] / 36525.0
        out[b] = dict(v=v, s=1.0 / v, T=360.0 / v / 360.0, f=v / (1 + v))
    return out


def sec_scale():
    S = scales()
    print("=" * 84)
    print("١ — التحويل قسمة، والمقياس مقلوب السرعة")
    print("=" * 84)
    print("\nالتحويل:  θ = P ÷ s   (s: نقاط لكل درجة).  والدورة تُقاس بوحدة 360 يومًا.\n")
    print(f"{'الكوكب':<9}{'v °/يوم':>10}{'الدورة يومًا':>14}{'الدورة/360':>12}"
          f"{'s = 1/v':>10}{'فى الخطاب':>11}")
    for b in BODIES:
        S_ = S[b]
        g = GANES.get(b, "")
        print(f"{AR[b]:<9}{S_['v']:>10.4f}{360 / S_['v']:>14.1f}{S_['T']:>12.3f}"
              f"{S_['s']:>10.3f}{str(g):>11}")
    print("\n  ⇒ الأرقام 1 و12 و30 التى كتبها ليست اختيارًا: هى سرعة الشمس والمشترى وزحل.")
    print("      و«45» و«40» ليست لكوكب — هى 360/8 ونصفها، أى كسور دائرة لا أجرام.")

    print("\n" + "=" * 84)
    print("٢ — السعر 8729 عبر مقاييسه الأربعة (يقابل النصّ بالحرف)")
    print("=" * 84)
    print(f"\n{'المقياس':<18}{'8729 ÷ s':>13}{'الدرجة':>10}{'البرج':>20}{'كتب جان':>18}")
    for label, s, claim in (("1 نقطة", 1, "29° الجوزاء"), ("30 نقطة (زحل)", 30, "21° الجدى"),
                            ("12 نقطة (المشترى)", 12, "7° 30' الحمل"),
                            ("1 سنت", 0.01, "27° 6' الجوزاء")):
        q = 8729 / s
        d = q % 360
        print(f"{label:<18}{q:>13.2f}{d:>10.2f}{A.sign_notation(d):>20}{claim:>18}")
    print("\n  ثلاثة من أربعة تطابق. والرابع (السنت) ينكسر: 8729 ÷ 0.01 = 872900 ≡ 260°،")
    print("  والمكتوب 87.1°. والعدد 87.29 هو 8729 ÷ 100 لا ÷ 0.01 — فالمقياس هنا **قسمة على 100**،")
    print("  أى أن السنت عنده وحدة قراءة لا مقياسًا. والخطأ المتبقّى 2° فى نصّه وحده.")


def sec_identity():
    print("\n" + "=" * 84)
    print("٣ — الهُوية: مقياس الكوكب = «1 نقطة = 1 يوم» على دائرة أخرى")
    print("=" * 84)
    S = scales()
    print(f"\n{'الكوكب':<9}{'s':>9}{'s × 360':>11}{'دورته يومًا':>14}{'الفرق':>9}")
    for b in ("earth", "mars", "jupiter", "saturn"):
        q = S[b]["s"] * 360
        d = 360 / S[b]["v"]
        print(f"{AR[b]:<9}{S[b]['s']:>9.3f}{q:>11.1f}{d:>14.1f}{q - d:>+9.2f}")
    print("\n  ⇒ الأسطر متساوية بالبناء: s×360 = الدورة بالأيام. فكل مقاييس الكواكب")
    print("     تقول الشىء نفسه: **نقطة واحدة = يوم واحد**. ويختلف حجم الدائرة فقط.")
    print("\n  والنتيجة: درجة السعر المقطوعة = (P−P₀)/s، ودرجة الكوكب = (t−t₀)/s.")
    print("     يتساويان ⟺ P − P₀ = t − t₀.  فالمقياس لا يضيف شرطًا؛ يُلغى من الطرفين.")

    a = A.date_to_jd(1931, 4, 16)
    b = A.date_to_jd(1954, 3, 19)
    days = b - a
    pts = COFFEE_HIGH - COFFEE_LOW
    print("\n  وشهادة خطاب البنّ نفسه:\n")
    print(f"    القاع {COFFEE_LOW:.0f} (16/4/1931) → القمة {COFFEE_HIGH:.0f} (19/3/1954)")
    print(f"    النقاط {pts:.0f} · الأيام {days:.0f} · 23 سنة × 360 = {23 * 360}")
    print(f"    النسبة: {pts / days:.4f} نقطة/يوم (بالأيام الحقيقية) · "
          f"{pts / (23 * 360):.4f} (بالسنة 360 يومًا)")
    print(f"    وخط 45° عنده: 435 + 8280 = 8715 · والقمة 8729 — فرق 14 نقطة = "
          f"{100 * (COFFEE_HIGH - 8715) / COFFEE_HIGH:.2f}%")
    print("\n  ⇒ 23 سنة من الصعود، 8294 نقطة فى 8280 يومًا مثاليًّا. **التربيع تحقّق.**")


def sec_saturn():
    print("\n" + "=" * 84)
    print("٤ — والاختبار المضاد: أرقام زحل فى الخطاب نفسه")
    print("=" * 84)
    print("\nثلاثة عشر رقمًا فى صفحتين، وفيهم خمسة أسعار منسوبة إلى درجات زحل المكتسبة.\n")
    print(f"{'الدرجة':>9}{'السعر':>8}{'المقياس الضمنى':>16}{'بـ s=30':>10}")
    for moved, price in ((287.25, 8632), (223.0, 7150), (176.733, 5940), (176.233, 5842),
                         (285.633, 8572), (233.0, 7230), (181.583, 6990)):
        print(f"{moved:>9.2f}{price:>8}{price / moved:>16.2f}{moved * 30:>10.0f}")
    print("\n  مقياسان يطابقان 30 بالضبط (30.01 و30.05)، وخمسة تنتشر من 31 إلى 38.5.")
    print("  ⇒ المقياس 30 صحيح كأصل، لكنه **لا يُطبَّق بثبات** — حتى داخل خطاب واحد.")


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


def sec_market(path, min_rows):
    data = load(path, min_rows)
    S = scales()
    print("\n" + "=" * 84)
    print("٥ — هل «1 نقطة = 1 يوم» فى السوق المصرى؟")
    print("=" * 84)
    r, rn = [], []
    for t, v in data.items():
        px = np.array(list(v.values()), float)
        n = len(px)
        if n < 300:
            continue
        r.append((px.max() - px.min()) / n)
        rn.append((px.max() - px.min()) / n / px.mean())
    r = np.array(r)
    print(f"\n{len(r)} سهمًا · المدى الكامل ÷ الأيام:\n")
    print(f"  الوسيط {np.median(r):.4f} نقطة/يوم · الربيعى {np.percentile(r, 25):.4f} – "
          f"{np.percentile(r, 75):.4f}")
    print(f"  المطلوب 1.000 ⇒ الفارق ×{1 / np.median(r):.0f}")
    print(f"  وبالقرش (×100): {100 * np.median(r):.3f} نقطة/يوم\n")
    print("  ⇒ الشرط P − P₀ = t − t₀ لا يتحقق بلا إعادة قياس. وإعادة القياس هى الحرّية")
    print("     التى قِيست فى §23: 966 بابًا، فيمرّ السعر من أحدها.")

    print("\n" + "=" * 84)
    print("٦ — والاختبار الحاسم: مقياس الكوكب «لنفسه» مقابل مقاييس غيره")
    print("=" * 84)
    PLN = ("mercury", "venus", "mars", "jupiter", "saturn")
    ASP = (0, 45, 60, 90, 120, 135, 180)
    cache = {}

    def lam(b, d):
        k = (b, d)
        if k not in cache:
            j = A.date_to_jd(*map(int, d.split("-")))
            cache[k] = A.longitude(b, j, "geo") * A.R2D
        return cache[k]

    def near(th, lon):
        x = abs((th - lon) % 360)
        x = min(x, 360 - x)
        return min(abs(x - a) for a in ASP)

    rows = []
    for t, v in data.items():
        ds, px = list(v), list(v.values())
        for i in range(260, len(ds), 13):
            rows.append((ds[i], px[i]))
    print(f"\nعينات {len(rows):,} · 1:1 · ±3° · 7 أوجه\n")
    print(f"{'الكوكب':<9}" + "".join(f"{AR[p][:7]:>9}" for p in PLN) + "   ← الأعمدة: المقياس")
    M = np.zeros((len(PLN), len(PLN)))
    for i, p in enumerate(PLN):
        line = f"{AR[p]:<9}"
        for j, q in enumerate(PLN):
            hit = sum(1 for d, pr in rows if near((pr / S[q]["s"]) % 360.0, lam(p, d)) <= 3.0)
            M[i, j] = 100.0 * hit / len(rows)
            line += f"{M[i, j]:>9.1f}"
        print(line)
    print(f"\n  القطر (مقياس الكوكب لكوكبه): {np.mean(np.diag(M)):.2f}%")
    print(f"  خارجه:                       {np.mean(M[~np.eye(len(PLN), dtype=bool)]):.2f}%")
    print("\n  لا ميزة. وهذا متوقَّع بعد §٣: المقياس يُلغى من الطرفين، فلا يفضّل كوكبًا.")
    print("  فمن ظنّ أن لكل كوكب مقياسًا يُقرّبه من نفسه، فقد ظنّ أن الأداة تُغيّر المقيس.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--min-rows", type=int, default=300)
    ns = ap.parse_args()
    sec_scale()
    sec_identity()
    sec_saturn()
    if ns.csv:
        sec_market(ns.csv, ns.min_rows)


if __name__ == "__main__":
    main()
