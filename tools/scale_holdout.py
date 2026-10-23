#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
المقياس المناسب لكل كوكب — هل يوجد؟ اختبارٌ خارج العينة على الأسهم المصرية.

السؤال الذى يجيب عنه هذا الملف وحده:

    إذا كان تحويل السعر إلى درجة هو θ = P ÷ s، فهل لكل كوكب مقياسٌ s
    يجعل درجة السعر «تواكب» ذلك الكوكب — أى يسقط على أوجهه أكثر من غيره؟

ومنهجان، والفرق بينهما هو الفرق بين العلم والتقاط:

    أ  المقياس المشتق  s = 1/v = الدورة ÷ 360     (لا حرّية فيه)
       يُطبَّق على كل الأسهم كما هو، ويُقاس.

    ب  المقياس المُوفَّق  s يُبحث عنه لكل سهم على حدة (200 قيمة)
       على 1998–2018، ثم يُقرأ على 2019–2025 **مرة واحدة**.

وفى (ب) مكيدة لا تُرى: مع 200 مقياس لكل سهم، سيجد البحث شيئًا دائمًا
فى العينة التى رُشِّح عليها. فالسؤال ليس «هل وجد؟» بل **«هل ما وجده يبقى؟»**.

القياس: نسبة الأيام التى تقع فيها θ داخل ±3° من وجه لأحد الكواكب الخمسة
الظاهرة (عطارد · الزهرة · المريخ · المشترى · زحل) — مركزية أرضية.

التشغيل:
    python3 tools/scale_holdout.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv
import math
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import astro_conjunctions as A  # noqa: E402

ASPECTS = (0.0, 45.0, 60.0, 90.0, 120.0, 135.0, 180.0)
PLANETS = ("mercury", "venus", "mars", "jupiter", "saturn")
AR = {"mercury": "عطارد", "venus": "الزهرة", "mars": "المريخ",
      "jupiter": "المشترى", "saturn": "زحل"}
TRAIN = ("1998-01-01", "2018-12-31")
TEST = ("2019-01-01", "2025-12-31")
ORB = 3.0
def _coverage():
    """نسبة [0°,180°] التى تقع داخل ±ORB من وجه — هى مستوى الصدفة."""
    cov = sum(min(180.0, a + ORB) - max(0.0, a - ORB) for a in ASPECTS)
    return 100.0 * cov / 180.0


CHANCE = _coverage()


#  ─────────────────────────────────────────────────────────────────────
#  البيانات والفلك
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


def longitude(body, date):
    jd = A.date_to_jd(*map(int, date.split("-")))
    T = (jd - 2451545.0) / 36525.0
    prec = (5029.0966 * T + 1.11113 * T * T) / 3600.0
    return (A.longitude(body, jd, "geo") * A.R2D + prec) % 360.0


def aspect_distance(theta, lon):
    """أقرب وجه. theta: (أيام,) أو (أيام × مقاييس) · lon: (أيام,) ⇒ الشكل نفسه."""
    theta = np.asarray(theta, float)
    if theta.ndim == 1:
        sep = np.mod(theta - lon, 360.0)
    else:
        sep = np.mod(theta - np.asarray(lon, float)[:, None], 360.0)
    sep = np.minimum(sep, 360.0 - sep)
    return np.min(np.abs(sep[..., None] - np.array(ASPECTS)), axis=-1)


#  ─────────────────────────────────────────────────────────────────────
#  أ — المقياس المشتق
#  ─────────────────────────────────────────────────────────────────────


def natural_scales():
    return {b: 360.0 / (A.ELEMENTS[b][1][3] / 36525.0) / 360.0 for b in PLANETS}


def sec_derived(data):
    print("=" * 92)
    print("أ — المقياس المشتق s = 1/v = الدورة ÷ 360:  يُطبَّق كما هو، بلا حرّية")
    print("=" * 92)
    S = natural_scales()
    print(f"\n{'الكوكب':<9}{'v °/يوم':>10}{'الدورة يومًا':>14}{'s = 1/v':>10}"
          f"{'s×360':>10}")
    for b in PLANETS:
        v = A.ELEMENTS[b][1][3] / 36525.0
        print(f"{AR[b]:<9}{v:>10.4f}{360 / v:>14.1f}{S[b]:>10.3f}{S[b] * 360:>10.0f}")
    print("\n  والعمودان الأخيران متساويان بالبناء: إعداد المقياس فى الدورة الكاملة")
    print("  يساوى عدد أيام الدورة. ⇒ كل مقياس كوكبى يعنى **نقطة واحدة = يوم واحد**.")

    dates = sorted({d for v in data.values() for d in v if d >= "1998-01-01"})
    cache = {b: np.array([longitude(b, d) for d in dates]) for b in PLANETS}
    di = {d: i for i, d in enumerate(dates)}

    print(f"\nالأرشيف: {len(data)} سهمًا · {len(dates)} يومًا (1998–2025)\n")
    print(f"{'الكوكب':<9}{'على وجهه':>11}{'ضابط (درجة عشوائية)':>22}{'الفرق':>9}")
    rng = np.random.default_rng(11)
    for b in PLANETS:
        hit = tot = 0
        ctrl = 0
        for v in data.values():
            ds = [d for d in v if d >= "1998-01-01"]
            if len(ds) < 300:
                continue
            px = np.array([v[d] for d in ds], float)
            idx = np.array([di[d] for d in ds])
            th = (px / S[b]) % 360.0
            d1 = aspect_distance(th, cache[b][idx])
            hit += int(np.sum(d1 <= ORB))
            tot += len(ds)
            th2 = rng.uniform(0, 360, len(ds))
            d2 = aspect_distance(th2, cache[b][idx])
            ctrl += int(np.sum(d2 <= ORB))
        p = 100.0 * hit / tot
        q = 100.0 * ctrl / tot
        print(f"{AR[b]:<9}{p:>10.1f}%{q:>20.1f}%{p - q:>+9.1f}")
    print(f"\n  ومستوى الصدفة = {CHANCE:.1f}% — لأن المسافة تُقاس على [0°,180°]،")
    print(f"  والأوجه السبعة تغطى 36° منها (±{ORB:g}° لكل وجه).")


#  ─────────────────────────────────────────────────────────────────────
#  ب — المقياس المُوفَّق
#  ─────────────────────────────────────────────────────────────────────


def sec_fitted(data, grid, planet):
    print("\n" + "=" * 92)
    print(f"ب — المقياس المُوفَّق: {len(grid)} مقياسًا لكل سهم، تدريبٌ ثم تحقّق — الكوكب: {AR[planet]}")
    print("=" * 92)
    dates = sorted({d for v in data.values() for d in v if d >= "1998-01-01"})
    di = {d: i for i, d in enumerate(dates)}
    lons = np.array([longitude(planet, d) for d in dates])

    tr, te, best_s, rnd_te, best_tr = [], [], [], [], []
    rng = np.random.default_rng(29)
    for v in data.values():
        ds = [d for d in v if d >= "1998-01-01"]
        if len(ds) < 500:
            continue
        px = np.array([v[d] for d in ds], float)
        idx = np.array([di[d] for d in ds])
        lon = lons[idx]
        yy = np.array([d[:4] for d in ds])
        trm = yy <= "2018"
        tem = yy >= "2019"
        if trm.sum() < 250 or tem.sum() < 120:
            continue
        #  مصفوفة (أيام × مقاييس): نصف قطر الدرجة
        th = np.mod(px[:, None] / grid[None, :], 360.0)
        dist = aspect_distance(th, lon)
        ok = dist <= ORB
        h_tr = ok[trm].mean(axis=0)
        h_te = ok[tem].mean(axis=0)
        k = int(np.argmax(h_tr))
        best_s.append(grid[k])
        best_tr.append(h_tr[k])
        tr.append(h_tr.mean())
        te.append(h_te[k])
        rnd_te.append(float(h_te[rng.integers(0, len(grid))]))

    tr, te = np.array(tr), np.array(te)
    best_tr, best_s = np.array(best_tr), np.array(best_s)
    rnd_te = np.array(rnd_te)
    n = len(tr)
    print(f"\nأسهم دخلت الاختبار: {n} · المقاييس المبحوثة: {len(grid)}")
    print(f"المدى: من {grid[0]:.4f} إلى {grid[-1]:.1f} خطوة هندسية ×{grid[1] / grid[0]:.3f}\n")
    print(f"{'':<28}{'التدريب':>12}{'التحقّق':>12}{'الفرق':>10}")
    print(f"{'متوسط كل المقاييس':<28}{100 * tr.mean():>11.1f}%{100 * rnd_te.mean():>11.1f}%"
          f"{100 * (rnd_te.mean() - tr.mean()):>+9.1f}")
    print(f"{'المقياس الأفضل فى التدريب':<28}{100 * best_tr.mean():>11.1f}%{100 * te.mean():>11.1f}%"
          f"{100 * (te.mean() - best_tr.mean()):>+9.1f}")
    print(f"\n  ▼ **المقارنة الصحيحة هى بمستوى الصدفة {CHANCE:.1f}%، لا بمقياس عشوائى.**")
    print(f"    التحقّق {100 * te.mean():.1f}%  مقابل  الصدفة {CHANCE:.1f}%"
          f"  ⇒ {100 * (te.mean() - CHANCE / 100):+.1f} نقطة")
    z = (te - CHANCE / 100)
    print(f"    t = {z.mean() / (z.std(ddof=1) / math.sqrt(n)):+.2f}  (n = {n}) · "
          f"وأسهم فوق الصدفة: {100 * np.mean(z > 0):.1f}%")
    print(f"\n    وأثرٌ لا بد من كشفه: المقاييس الكبيرة جدًّا تُسقط السعر إلى قرب 0° —")
    print(f"    فيصير «اقترانًا» دائمًا. ولذلك متوسط العشوائى {100 * rnd_te.mean():.1f}%"
          f" ≠ الصدفة.")
    print(f"    والمقياس المختار فى التدريب نجح لأنه تجنّب هذا الطرف، لا لأنه واكب الكوكب.")

    print(f"\nتوزيع المقياس المختار (المقياس الأفضل لكل سهم):")
    qs = np.percentile(best_s, [5, 25, 50, 75, 95])
    print(f"  المئينات 5/25/50/75/95: {qs[0]:.3f} · {qs[1]:.3f} · {qs[2]:.3f} · "
          f"{qs[3]:.3f} · {qs[4]:.3f}")
    print("  ⇒ لو كان للسهم مقياسٌ واحد صحيح، لَتجمّعت هذه القيم عنده.")
    print("     وهى منتشرة على مدى أربع مراتب — أى أن البحث يختار ما يناسب عيّنته.")
    return best_s


#  ─────────────────────────────────────────────────────────────────────
#  ج — الهُوية
#  ─────────────────────────────────────────────────────────────────────


def sec_identity(data):
    print("\n" + "=" * 92)
    print("ج — الشرط الذى يعنيه المقياس: P − P₀ = t − t₀")
    print("=" * 92)
    print("""
    درجة السعر المقطوعة  = (P − P₀)/s
    درجة الكوكب المقطوعة = (t − t₀)/s

    يتساويان  ⟺  P − P₀ = t − t₀        (فالمقياس يُلغى من الطرفين)
""")
    r = []
    for t, v in data.items():
        px = np.array([x for x in v.values() if x > 0], float)
        if len(px) < 300:
            continue
        r.append((px.max() - px.min()) / len(px))
    r = np.array(r)
    print(f"  فى الأرشيف: {len(r)} سهمًا · (المدى ÷ الأيام):")
    for q in (10, 25, 50, 75, 90):
        print(f"     مئين {q:2d}: {np.percentile(r, q):8.4f} نقطة/يوم"
              f"   ⇒ 1/{1 / np.percentile(r, q):,.0f}")
    print(f"\n  والشرط يقتضى 1.000. والوسيط {np.median(r):.4f} ⇒ **×{1 / np.median(r):,.0f}**.")
    print("  وبالقرش (×100): "
          f"{100 * np.median(r):.3f} نقطة/يوم — أى ×{1 / (100 * np.median(r)):.1f}.")
    print("\n  ⇒ لا سهم مصرى يتحقق فيه الشرط بالمقياس 1. وإذا أُريد إجبارُه،")
    print("     لزم لكل سهم مقياسُه الخاص — وهو ما اختُبر فى (ب) وسقط.")


#  ─────────────────────────────────────────────────────────────────────


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--min-rows", type=int, default=300)
    ap.add_argument("--planet", default="jupiter", choices=list(PLANETS))
    ap.add_argument("--grid", type=int, default=200)
    ns = ap.parse_args()

    if not ns.csv:
        print(__doc__)
        return
    data = load(ns.csv, ns.min_rows)
    grid = np.logspace(math.log10(1e-3), math.log10(3e3), ns.grid)
    sec_derived(data)
    sec_fitted(data, grid, ns.planet)
    sec_identity(data)


if __name__ == "__main__":
    main()
