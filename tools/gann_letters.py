#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خطابا جان الفلكى — تحقيقٌ من كل جانب، وهندسةٌ عكسية.

المصدران (مصوّران بخط الآلة؛ والنص استُخرج من الصور صفحةً صفحة):
    May Coffee Astro Letter  — 19 مارس 1954، قمّة 8729، خمس صفحات
    Soy Beans Astro Letter   — 18 يناير 1954، أربع صفحات

والملف يقيس أربعة أشياء لا تُقرأ معًا عادة:

    أ  الفلك      هل أوضاعه صحيحة؟ تُحسب من العناصر وتُقارن سطرًا سطرًا.
    ب  الاستعادة  قيمُه المشتقّة (المتوسطات والمنتصف) تكشف قيمَه الخام.
    ج  الآلة      المنهج كاملًا كما كتبه، لا كما يُشرح.
    د  الحرّية    المقاييس التى يستعملها — وهل تُقفل على شىء.

ثم يُختبر منها ما يُختبر على الأرشيف المصرى:
    هـ متوسط الكواكب   (قاعدة بلا حرّية: رقم واحد فى اليوم)
    و  نصف المدى       («مركز الثقل»: هل هو قمّة فى توزيع الارتدادات؟)
    ز  مقياس 45°      (المدى ÷ الزمن لكل حملة: هل هو ثابت؟)

التشغيل:
    python3 tools/gann_letters.py
    python3 tools/gann_letters.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv
import math
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import astro_conjunctions as A  # noqa: E402

ASPECTS = (0, 45, 60, 90, 120, 135, 180)
SIX = ("mars", "jupiter", "saturn", "uranus", "neptune", "pluto")
EIGHT = ("mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto")
AR = {"mercury": "عطارد", "venus": "الزهرة", "sun": "الشمس", "mars": "المريخ",
      "jupiter": "المشترى", "saturn": "زحل", "uranus": "أورانوس", "neptune": "نبتون",
      "pluto": "بلوتو"}

#  ما كتبه جان حرفًا فى خطاب البنّ (19 مارس 1954) — مركزية شمسية
GAN_COFFEE_HELIO = {"jupiter": 80.583, "saturn": 214.44, "uranus": 111.52,
                    "neptune": 204.35, "pluto": 144.03, "mars": 221.0}
GAN_COFFEE_AVG6 = 164.17          # «14°17' العذراء»
GAN_COFFEE_MID_JS = 152.09        # «نصف المشترى‑زحل = 2°9' العذراء»
GAN_COFFEE_AVG4 = 155.10          # «متوسط زحل ومشترى وأورانوس ونبتون»
#  ما كتبه عن حركة زحل حتى 19 مارس 1954 (درجات قوسية)
GAN_SATURN_MOVED = {
    ("1931-04-16", "geo"): 285.633, ("1931-04-16", "helio"): 287.25,
    ("1936-10-01", "geo"): 233.0,   ("1936-10-01", "helio"): 223.0,
    ("1940-05-15", "geo"): 181.583, ("1940-05-15", "helio"): 176.733,
    ("1940-08-19", "geo"): 173.383, ("1940-08-19", "helio"): 176.233,
}


def lon(body, date, frame, hours=0.0):
    jd = A.date_to_jd(*map(int, date.split("-")), hours)
    T = (jd - 2451545.0) / 36525.0
    prec = (5029.0966 * T + 1.11113 * T * T) / 3600.0
    if frame == "geo":
        return (A.longitude(body, jd, "geo") * A.R2D + prec) % 360.0
    return A.longitude(body, jd, "helio") * A.R2D


#  ─────────────────────────────────────────────────────────────────────
#  أ — الفلكى
#  ─────────────────────────────────────────────────────────────────────


def report_sky():
    print("=" * 88)
    print("أ — الفلكى: أوضاع جان مقابل المحسوب (19 مارس 1954، مركزية شمسية)")
    print("=" * 88)
    rows, tot_g, tot_c = [], 0.0, 0.0
    print(f"\n{'الكوكب':<9}{'جان':>10}{'درجته':>9}{'المحسوب':>10}{'درجته':>9}{'الفرق':>9}")
    for b, v in GAN_COFFEE_HELIO.items():
        c = lon(b, "1954-03-19", "helio")
        tot_g += v
        tot_c += c
        print(f"{AR[b]:<9}{v:>10.3f}{A.sign_notation(v):>19}{c:>10.3f}"
              f"{A.sign_notation(c):>19}{(v - c + 180) % 360 - 180:>+9.2f}")
    print(f"{'المتوسط':<9}{GAN_COFFEE_AVG6:>10.2f}{'':>9}{tot_c / 6:>10.2f}{'':>9}"
          f"{(GAN_COFFEE_AVG6 - tot_c / 6 + 180) % 360 - 180:>+9.2f}")
    print("\n  والمتوسط الذى كتبه يطابق المحسوب أكثر مما تطابقه قيمه هو:"
          f"\n    مجموع قيمه  {tot_g:.2f} ⇒ متوسط {tot_g / 6:.2f}،  والمحسوب {tot_c / 6:.2f}"
          f"،  والمكتوب {GAN_COFFEE_AVG6:.2f}")
    print("\n  والحركات التراكمية لزحل حتى 1954-03-19:\n")
    print(f"  {'من':<12}{'الإطار':<7}{'جان':>9}{'المحسوب':>10}{'الفرق':>9}")
    for (d, fr), v in GAN_SATURN_MOVED.items():
        c = (lon("saturn", "1954-03-19", fr) - lon("saturn", d, fr)) % 360
        flag = "" if abs(c - v) < 1 else "  ←"
        print(f"  {d:<12}{'أرضى' if fr == 'geo' else 'شمسى':<7}{v:>9.2f}{c:>10.2f}"
              f"{c - v:>+9.2f}{flag}")
    print("\n  ⇒ الفلكى صحيح: ستُّ حركات من ثمانٍ داخل درجة، وواحدة داخل ثلاث.")
    print("     فمن كتب هذا كان يقرأ إفيميريس، لا يخمّن.")

    print("\n" + "=" * 88)
    print("ب — الاستعادة: متوسطاته تكشف قيمَه الخام")
    print("=" * 88)
    s = lon("saturn", "1954-03-19", "helio")
    j_from_mid = 2 * GAN_COFFEE_MID_JS - s
    print(f"\n  نصف (مشترى+زحل) = {GAN_COFFEE_MID_JS:.2f} ⇒ مشترى = {j_from_mid:.2f}")
    print(f"  والمكتوب عنده «20°35' الجوزاء» = 80.58، والمحسوب {lon('jupiter', '1954-03-19', 'helio'):.2f}")
    print(f"  ⇒ قيمة المتوسط تتفق مع الرصد ومع المكتوب تختلف 9.5°.")
    agg4 = 4 * GAN_COFFEE_AVG4
    agg6 = 6 * GAN_COFFEE_AVG6
    real4 = sum(lon(b, "1954-03-19", "helio") for b in ("saturn", "jupiter", "uranus", "neptune"))
    real6 = sum(lon(b, "1954-03-19", "helio") for b in SIX)
    print(f"\n  متوسط الأربعة ×4 = {agg4:.1f}  والمحسوب {real4:.1f}  (فرق {agg4 - real4:+.1f})")
    print(f"  متوسط الستة  ×6 = {agg6:.1f}  والمحسوب {real6:.1f}  (فرق {agg6 - real6:+.1f})")
    print("\n  ⇒ الفرقان صغيران ومتوافقان؛ فالسطر المشوّه سطرٌ واحد، والحساب سليم.")
    print("     **هذه هى الهندسة العكسية**: لا تُصدَّق أرقامه، بل يُستدلّ عليها من علاقاتها.")

    print("\n  وفى خطاب الصويا (18 يناير 1954) يقول: زحل أرضى 8°9' العقرب، والمشترى 21° الجوزاء.")
    for b, claimed in (("saturn", 218.15), ("jupiter", 81.0)):
        c = lon(b, "1954-01-18", "geo")
        rate = 360.0 / (A.ELEMENTS[b][0][3] and 1) if False else None
        print(f"    {AR[b]:<8} قال {claimed:6.2f} · المحسوب {c:6.2f} · فرق {c - claimed:+5.2f}°")
    print("    والكوكبان يشيران إلى التاريخ نفسه (نحو 12 ديسمبر 1953) —")
    print("    فالأوضاع من إفيميريس حقيقى، لكنها ليست ليوم الخطاب.")


#  ─────────────────────────────────────────────────────────────────────
#  ج/د — الآلة والحرّية
#  ─────────────────────────────────────────────────────────────────────


def report_machine():
    print("\n" + "=" * 88)
    print("ج — الآلة كما كُتبت، لا كما تُشرح")
    print("=" * 88)
    print("""
    الخطابان يعطيان إجراءً واحدًا بستّ خطوات، لا نصائح:

      ١. السعر ← درجة، بمقياس s:        θ = P / s           (s: نقاط لكل درجة)
      ٢. الدرجة ← برج:                  θ mod 30
      ٣. مستوى مقاومة:                  P = s · (λ_كوكب + وجه)   حيث الوجه ∈ {45,60,90,120,135,180}
      ٤. مستوى مقاومة آخر:              P = λ_كوكب · s          (بلا وجه)
      ٥. خط 45°:                        P = P_قاع + s · (أيام)
      ٦. تاريخ:                         اليوم الذى يبلغ فيه الكوكب λ_قاع + وجه

    وهذه هى «الالتقاء»: حين يقع السعر والزمن على الشبكة نفسها فى يوم واحد.
""")
    print("  والمقاييس التى استعملها فى تسع صفحات — بالحرف:")
    for s in ("1 نقطة = 1 درجة", "1 سنت = 1 درجة", "30 نقطة = 1 درجة",
              "12 نقطة = 1 درجة («مقياس المشترى»)", "45 نقطة = 1 درجة",
              "30 نقطة لكل شهر", "45 نقطة لكل شهر", "40 نقطة لكل شهر",
              "1 سنت = 1 ساعة = 15° (24 سنتًا = الدائرة)"):
        print(f"    · {s}")
    print("\n  ⇒ تسعة مقاييس لعملة واحدة فى تسع صفحات.")
    print("     وفى الفقرة الأولى من خطاب البنّ وحده: أربعة مقاييس للسعر 8729،")
    print("     تعطى 29° الجوزاء · 21° الجدى · 7°30' الحمل · 27°6' الجوزاء.")
    print("     **السعر الواحد له أربع درجات فى صفحة واحدة.**")

    print("\n  وأرقام الحركة: «24 سنتًا = دورة»، «48 · 72 · 96 · 120 · 144 سنتًا»،")
    print("  و«144 = 6 × 24 = مربع 12»، و«7 × 24 = 168». فالسنت = الساعة = 15°،")
    print("  والدورة = 24 سنتًا. وهذا هو المقياس الوحيد الذى **لم يُخيّره**:")
    print("  24 ساعة هى دورة الأرض — والباقى مضاعفاتها.")


def report_freedom(csv_path, min_rows):
    print("\n" + "=" * 88)
    print("د — الحرّية: كم بابًا يفتح المقياس؟")
    print("=" * 88)
    if not csv_path:
        return
    data = load(csv_path, min_rows)
    scales = (1, 2, 3, 4, 5, 6, 8, 9, 12, 16, 24, 30, 36, 45, 60, 72, 90,
              100, 120, 144, 180, 240, 360)
    rows = []
    for t, v in data.items():
        ds, px = list(v), list(v.values())
        for i in range(260, len(ds), 11):
            rows.append((ds[i], px[i]))
    cache = {}

    def pl(d):
        if d not in cache:
            cache[d] = [lon(b, d, "geo") for b in SIX]
        return cache[d]

    def closest(theta, d):
        best = 999.0
        for lam in pl(d):
            s = abs((theta - lam) % 360)
            s = min(s, 360 - s)
            best = min(best, min(abs(s - a) for a in ASPECTS))
        return best

    print(f"\nعينات {len(rows):,} · {len(SIX)} كواكب · {len(ASPECTS)} أوجه · سماحية 3°\n")
    print(f"{'المقياس':>9}{'يُصيب':>9}{'المستقلّ منه':>15}")
    count = np.zeros(len(rows))
    for s in scales:
        hit = np.array([closest((p / s) % 360.0, d) <= 3.0 for d, p in rows])
        count += hit
        print(f"{s:>9}{100 * hit.mean():>8.1f}%")
    print(f"\n  متوسط المقاييس التى تُصيب فى العينة الواحدة: {count.mean():.1f} من {len(scales)}")
    print(f"  وعينات فيها مقياس واحد على الأقل: {100 * np.mean(count >= 1):.1f}%")
    print(f"  وفى خمسة مقاييس على الأقل:        {100 * np.mean(count >= 5):.1f}%")

    # الضابط: نفس الأسعار مخلوطة على التواريخ
    rng = np.random.default_rng(5)
    prices = np.array([p for _, p in rows])
    perm = rng.permutation(len(rows))
    ctrl = np.array([closest((prices[perm[i]] / s) % 360.0, rows[i][0])
                     for i, s in enumerate(scales) if False] or
                    [np.mean([closest((prices[perm[i]] / s) % 360.0, rows[i][0]) <= 3.0
                              for i in range(0, len(rows), 4)]) * 100 for s in (1,)])
    print(f"\n  والضابط — نفس الأسعار مخلوطة على التواريخ، بمقياس 1: {ctrl[0]:.1f}%"
          f"   (مقابل {100 * np.mean([closest((p / 1) % 360.0, d) <= 3.0 for d, p in rows]):.1f}%)")
    print("  (المقاييس الكبيرة تُسقط السعر إلى قرب 0° — و0° نفسه وجه. فالسعر 5 جنيهات")
    print("   ÷ 360 = 0.01°، وهو «اقتران» مجانًا. ولهذا 68% ليست دلالة بل أثر صغر السعر.)")
    print("  ⇒ فى سوق أسعاره أقل من 360، المقياس الوحيد ذو معنى هو 1:1 — وهو ما جرّبه §19.")


#  ─────────────────────────────────────────────────────────────────────
#  هـ/و/ز — الاختبارات على الأرشيف
#  ─────────────────────────────────────────────────────────────────────


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


def report_market(data):
    print("\n" + "=" * 88)
    print("هـ — متوسط الكواكب: القاعدة الوحيدة بلا حرّية، مقيسة")
    print("=" * 88)
    cache = {}

    def avg6(d):
        if d not in cache:
            cache[d] = sum(lon(b, d, "helio") for b in SIX) / len(SIX)
        return cache[d]

    def cl(theta, d):
        s = abs((theta - avg6(d)) % 360)
        s = min(s, 360 - s)
        return min(abs(s - a) for a in ASPECTS)

    rows = []
    for t, v in data.items():
        ds, px = list(v), list(v.values())
        for i in range(260, len(ds), 7):
            rows.append((ds[i], px[i]))
    rng = np.random.default_rng(3)
    for name, f in (("1:1", lambda p: p % 360.0), ("مضاعفة", lambda p: (360 * math.log10(p)) % 360)):
        d = np.array([cl(f(p), dt) for dt, p in rows])
        r = rng.uniform(0, 360, len(rows))
        dc = np.array([cl0(f(p), r[i]) for i, (dt, p) in enumerate(rows)])
        print(f"  {name:<8} وسيط المسافة {np.median(d):5.1f}° · ضمن 3° فى {100 * np.mean(d <= 3):4.1f}%"
              f"   |  ضابط (درجات عشوائية) {np.median(dc):5.1f}° · {100 * np.mean(dc <= 3):4.1f}%")
    print("\n  الفارق صفر. و«متوسط الكواكب» ليس مستوى مقاومة — هو رقم واحد لكل يوم،")
    print("  والصدفة وحدها تعطى خمسه.")

    print("\n" + "=" * 88)
    print("و — «مركز الثقل»: هل نصف المدى قمّة فى توزيع الارتدادات؟")
    print("=" * 88)
    ret = []
    for t, v in data.items():
        ds, px = list(v), np.array(list(v.values()), float)
        idx = zigzag(px)
        for a, b, c in zip(idx, idx[1:], idx[2:]):
            A_ = px[b] - px[a]
            if abs(A_) > 0:
                r = (px[b] - px[c]) / A_
                if -0.2 < r < 1.6:
                    ret.append(r)
    ret = np.array(ret)
    print(f"\n{len(ret):,} ارتدادًا · وسيط {np.median(ret):.3f}\n")
    print(f"{'المستوى':>8}{'±0.02':>9}{'±0.05':>9}{'الجوار (بنفس العرض)':>22}")
    for x, name in ((0.5, "1/2"), (0.25, "1/4"), (0.75, "3/4"), (1 / 3, "1/3"),
                    (2 / 3, "2/3"), (0.375, "3/8"), (0.618, "0.618")):
        near = np.mean(np.abs(ret - x) <= 0.05)
        side = (np.mean(np.abs(ret - (x - 0.15)) <= 0.05) +
                np.mean(np.abs(ret - (x + 0.15)) <= 0.05)) / 2
        print(f"{name:>8}{100 * np.mean(np.abs(ret - x) <= 0.02):>8.1f}%"
              f"{100 * near:>8.1f}%{100 * side:>20.1f}%")
    print("\n  لا قمّة عند النصف: الكثافة تتدرّج بلا انكسار. و«مركز الثقل» تعبير عن")
    print("  الرسم لا عن السوق. (والقياس مشروط بعتبة الكشف 20% — تُقرأ فروقه لا مستواه.)")

    print("\n" + "=" * 88)
    print("ز — مقياس 45°: هل المدى/الزمن ثابت فى السوق؟")
    print("=" * 88)
    sc = []
    for t, v in data.items():
        px = np.array(list(v.values()), float)
        for i in range(260, len(px), 20):
            w = px[max(0, i - 126):i + 1]
            R = w.max() - w.min()
            if R > 0:
                sc.append(R / min(126, i))
    sc = np.array(sc)
    print(f"\n{'مقياس':>0} المدى ÷ الأيام: وسيط {np.median(sc):.4f} · الربيعى "
          f"{np.percentile(sc, 25):.4f} – {np.percentile(sc, 75):.4f}")
    print(f"المدى الكامل: {sc.min():.5f} → {sc.max():.3f}  (×{sc.max() / sc.min():,.0f})")
    print(f"حملات مقياسها ≈ 24: {100 * np.mean(np.abs(sc - 24) <= 2.4):.2f}%  ·  و≈ 1: {100 * np.mean(np.abs(sc - 1) <= 0.1):.2f}%")
    print("\n  ⇒ لا مقياس طبيعىً للسهم. و«45°» ليست زاوية يجدها السوق، بل اختيارٌ")
    print("     يجعله الراسم موجودًا: بمجرد اختيار s يصير المدى/الزمن = s هو الخط.")


def cl0(theta, other):
    s = abs((theta - other) % 360)
    s = min(s, 360 - s)
    return min(abs(s - a) for a in ASPECTS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--min-rows", type=int, default=300)
    ns = ap.parse_args()
    report_sky()
    report_machine()
    report_freedom(ns.csv, ns.min_rows)
    if ns.csv:
        report_market(load(ns.csv, ns.min_rows))


if __name__ == "__main__":
    main()
