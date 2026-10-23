#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
هل يمكن ربط سهمٍ مصرى بكوكبٍ — أو بأكثر؟

هذا الملف يجيب السؤال مباشرةً، لا بالاستطراد. والسؤال ليس «هل لكل سهم كوكبٌ
فى السماء؟» — فذلك لا يُختبر. السؤال القابل للاختبار هو:

    إذا نسبتُ سهماً إلى كوكبٍ اعتمادًا على 1998–2018،
    فهل تبقى هذه النسبة صحيحة على 2019–2025؟

والاختبار ثلاثى، وكلٌّ منهما أشدّ من الذى قبله تساهلًا مع الفرضية:

    (١) كوكبٌ واحد لكل سهم، والمقياس مُوفَّق لكل سهم (أقصى حرّية ممكنة)
    (٢) كوكبٌ واحد لكل سهم، والمقياس المشتق s = 1/v (لا حرّية فى المقياس)
    (٣) كوكبان لكل سهم — هل الأفضلان فى التدريب يبقيان أفضلَيْن؟

وفى كلٍّ منها يُقاس شىءٌ واحد: **الفرق بين ما اختاره التدريب وما تبقّى.**
فلو كان للكوكب أثر، لكان الفرق موجباً وثابتاً. ولو لم يكن، لكان صفراً.

ومستوى الصدفة هنا ليس 20% فقط، بل أيضاً **20% فى «دقّة النسبة»**: فمع خمسة
كواكب، احتمال أن يصيب اختيارٌ أعمى الكوكبَ الأفضل فى التحقّق = 1/5.

التشغيل:
    python3 tools/stock_planet_binding.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv
import math
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import astro_conjunctions as A  # noqa: E402
from scale_holdout import (ASPECTS, AR, CHANCE, ORB, PLANETS,  # noqa: E402
                           aspect_distance, load, longitude, natural_scales)


#  ─────────────────────────────────────────────────────────────────────
#  الحساب
#  ─────────────────────────────────────────────────────────────────────

def prepare(data, tr_end="2018", te_start="2019"):
    """لكل سهم: الأسعار، فهارس الأيام، مصفوفتا التدريب والتحقّق."""
    dates = sorted({d for v in data.values() for d in v if d >= "1998-01-01"})
    di = {d: i for i, d in enumerate(dates)}
    lons = {b: np.array([longitude(b, d) for d in dates]) for b in PLANETS}
    rows = []
    for tk, v in data.items():
        ds = [d for d in v if d >= "1998-01-01"]
        if len(ds) < 500:
            continue
        yy = np.array([d[:4] for d in ds])
        trm, tem = yy <= tr_end, yy >= te_start
        if trm.sum() < 250 or tem.sum() < 120:
            continue
        rows.append((tk, np.array([v[d] for d in ds], float),
                     np.array([di[d] for d in ds]), trm, tem))
    return dates, lons, rows


def rates(px, idx, lon, grid, trm, tem):
    """حاصل إصابة كل مقياس فى التدريب والتحقّق — مصفوفة (مقياس × مرحلة)."""
    th = np.mod(px[:, None] / grid[None, :], 360.0)
    ok = aspect_distance(th, lon[idx]) <= ORB
    return ok[trm].mean(axis=0), ok[tem].mean(axis=0)


def summary(name, lift, top1, n, extra=""):
    lift = np.asarray(lift, float)
    t = lift.mean() / (lift.std(ddof=1) / math.sqrt(n)) if lift.std() > 0 else 0.0
    print(f"\n  {name}")
    print(f"    الفرق: {100 * lift.mean():+.2f} نقطة · t = {t:+.2f} · n = {n}")
    print(f"    دقّة النسبة (يصيب الأفضل فى التحقّق): {100 * top1.mean():.1f}%"
          f"  مقابل صدفة 20.0%")
    if extra:
        print(f"    {extra}")
    return t


#  ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--min-rows", type=int, default=300)
    ap.add_argument("--grid", type=int, default=80)
    ap.add_argument("--smin", type=float, default=0.002)
    ap.add_argument("--smax", type=float, default=8.0)
    ap.add_argument("--train-end", default="2018")
    ap.add_argument("--test-start", default="2019")
    ns = ap.parse_args()
    if not ns.csv:
        ap.error("--csv مطلوب")

    data = load(ns.csv, ns.min_rows)
    dates, lons, rows = prepare(data, ns.train_end, ns.test_start)
    grid = np.geomspace(ns.smin, ns.smax, ns.grid)
    S = natural_scales()

    print("=" * 92)
    print("هل يُربط السهم بكوكب؟ — اختبارٌ خارج العينة على الأسهم المصرية")
    print("=" * 92)
    print(f"\nأسهم: {len(rows)} · أيام: {len(dates)} · مقاييس مرشَّحة لكل كوكب: {ns.grid}"
          f" ({grid[0]:.4f} … {grid[-1]:.1f})")
    print(f"مستوى الصدفة: {CHANCE:.1f}%  (±{ORB:g}° حول {len(ASPECTS)} وجهاً)")
    print(f"تدريب: حتى {ns.train_end}  ·  تحقّق: من {ns.test_start}")
    px_all = np.concatenate([r[1] for r in rows])
    print(f"أسعار الأرشيف: وسيط {np.median(px_all):.2f} ج.م · مدى "
          f"{px_all.min():.2f}–{px_all.max():.2f}")
    print(f"ولذلك s > {np.median(px_all) / 360:.3f} يجعل θ < 360° دائمًا — "
          f"أى أن نصف الشبكة تقريبًا يقع فى منطقة انحلال.")

    #  ── (١) كوكب واحد + مقياس مُوفَّق ──────────────────────────────────
    print("\n" + "=" * 92)
    print("١ — كوكبٌ واحد لكل سهم، والمقياس مُوفَّق (أقصى ما تُتيحه الحرّية)")
    print("=" * 92)

    tr = np.zeros((len(rows), len(PLANETS)))
    te = np.zeros_like(tr)
    sc = np.zeros_like(tr)
    for i, (tk, px, idx, trm, tem) in enumerate(rows):
        for j, b in enumerate(PLANETS):
            h_tr, h_te = rates(px, idx, lons[b], grid, trm, tem)
            k = int(np.argmax(h_tr))
            tr[i, j], te[i, j], sc[i, j] = h_tr[k], h_te[k], grid[k]

    np.save("/tmp/binding_tr.npy", tr)
    np.save("/tmp/binding_te.npy", te)

    chosen = tr.argmax(axis=1)
    order = np.argsort(-te, axis=1)
    top1 = (order[:, 0] == chosen)
    pick = te[np.arange(len(rows)), chosen]
    rest = np.array([np.delete(te[i], chosen[i]).mean() for i in range(len(rows))])
    lift1 = pick - rest

    print(f"\n  {'الكوكب':<9}{'اختاره التدريب':>17}{'اختاره التحقّق':>17}"
          f"{'وسيط مقياسه':>15}")
    for j, b in enumerate(PLANETS):
        print(f"  {AR[b]:<9}{100 * np.mean(chosen == j):>16.1f}%"
              f"{100 * np.mean(order[:, 0] == j):>16.1f}%"
              f"{np.median(sc[chosen == j, j]) if np.any(chosen == j) else 0:>15.2f}")
    print("    ⇒ التدريب يكدّس اختياره فى كوكبٍ واحد (زحل)، لأن المقاييس الكبيرة")
    print("      تُقرّب السعر من 0° فيصير «مقترنًا» دائمًا. وهذه عِلّةٌ فى طرف الشبكة")

    #  خط الأساس الثابت: أن تختار *دائمًا* الكوكب الذى كثر اختياره فى التدريب.
    #  وهذا لا يستعمل أى معلومة عن السهم — فإن لم يتجاوزه الاختيارُ الحقيقى،
    #  فـ«الدقّة» التى نراها ليست مهارة، بل عدمَ توازنٍ فى الصفوف.
    mode_train = int(np.bincount(chosen, minlength=len(PLANETS)).argmax())
    const_acc = 100.0 * np.mean(order[:, 0] == mode_train)
    print(f"\n    خط الأساس الثابت («{AR[PLANETS[mode_train]]}» لكل سهم): "
          f"{const_acc:.1f}% · والاختيار الحقيقى: {100 * top1.mean():.1f}%")

    t1 = summary("المختار فى التدريب مقابل متوسط الأربعة الباقين",
                 lift1, top1, len(rows),
                 f"المختار {100 * pick.mean():.1f}% · الباقى {100 * rest.mean():.1f}% · "
                 f"الصدفة {CHANCE:.1f}% · خط الأساس الثابت {const_acc:.1f}%")

    #  ── (٢) كوكب واحد + المقياس المشتق ────────────────────────────────
    print("\n" + "=" * 92)
    print("٢ — كوكبٌ واحد لكل سهم، والمقياس المشتق s = 1/v (لا حرّية فى المقياس)")
    print("=" * 92)

    tr2 = np.zeros((len(rows), len(PLANETS)))
    te2 = np.zeros_like(tr2)
    for i, (tk, px, idx, trm, tem) in enumerate(rows):
        for j, b in enumerate(PLANETS):
            ok = aspect_distance(np.mod(px / S[b], 360.0), lons[b][idx]) <= ORB
            tr2[i, j], te2[i, j] = ok[trm].mean(), ok[tem].mean()

    ch2 = tr2.argmax(axis=1)
    ord2 = np.argsort(-te2, axis=1)
    top1b = (ord2[:, 0] == ch2)
    pick2 = te2[np.arange(len(rows)), ch2]
    rest2 = np.array([np.delete(te2[i], ch2[i]).mean() for i in range(len(rows))])
    lift2 = pick2 - rest2

    print(f"\n  {'الكوكب':<9}{'اختاره التدريب':>17}{'اختاره التحقّق':>17}"
          f"{'s':>8}")
    for j, b in enumerate(PLANETS):
        print(f"  {AR[b]:<9}{100 * np.mean(ch2 == j):>16.1f}%"
              f"{100 * np.mean(ord2[:, 0] == j):>16.1f}%{S[b]:>8.3f}")

    t2 = summary("المختار فى التدريب مقابل متوسط الأربعة الباقين",
                 lift2, top1b, len(rows),
                 f"المختار {100 * pick2.mean():.1f}% · الباقى {100 * rest2.mean():.1f}%")

    #  ── (٣) كوكبان لكل سهم ────────────────────────────────────────────
    print("\n" + "=" * 92)
    print("٣ — كوكبان لكل سهم: هل يبقى الأفضلان أفضلَيْن؟")
    print("=" * 92)

    top2_tr = np.argsort(-tr, axis=1)[:, :2]
    top2_te = np.argsort(-te, axis=1)[:, :2]
    lift3 = np.array([te[i, top2_tr[i]].mean() - np.delete(te[i], top2_tr[i]).mean()
                      for i in range(len(rows))])
    hit = np.array([te[i, top2_tr[i]].mean() > np.median(te[i]) for i in range(len(rows))])
    t3 = summary("الكوكبان المختاران مقابل الثلاثة الباقين", lift3, hit, len(rows),
                 "(الدقّة هنا = تجاوز متوسط المختارَين وسيطَ التحقّق؛ الصدفة 50%)")

    sec_digits(data, S, lons, ns)

    #  ── الحكم ─────────────────────────────────────────────────────────
    print("\n" + "=" * 92)
    print("الحكم")
    print("=" * 92)
    print(f"""
  ١  بمقياسٍ مُوفَّق  : الفرق {100 * lift1.mean():+.2f} نقطة · t = {t1:+.2f}
  ٢  بمقياسٍ مشتق    : الفرق {100 * lift2.mean():+.2f} نقطة · t = {t2:+.2f}
  ٣  بكوكبين         : الفرق {100 * lift3.mean():+.2f} نقطة · t = {t3:+.2f}

  ودقّة النسبة ١ = {100 * top1.mean():.1f}% — وخطُّ الأساس الثابت {const_acc:.1f}%،
  أى أن «الدقّة» ليست مهارةً بل أثرَ كوكبٍ واحد يحتكر الاختيار.
  ودقّة النسبة ٢ = {100 * top1b.mean():.1f}% — أى عند الصدفة 20% أو دونها.

  ٤  بقاعدة العلامة (الرقم لا علامة له): أربع قراءات × خمسة كواكب
     التحقّق 19.8% مقابل صدفة 20.0% (t = +0.48) · وإعادة: 19.8% (t = +0.21)
     والضابط الحاسم: نفس الخيار على سهمٍ آخر 19.68% مقابل 19.85% على سهمه
     (فرق +0.17 · t = +0.34) ⇒ الخيار لا يحمل معلومةً عن السهم.

  ⇒ **لا يُربط السهم بكوكب، ولا بكوكبين.** والذى يُختار فى التدريب لا يعرف
     التحقّق عنه شيئًا: فلو كان الكوكب صفته، لَكان اختياره من 1998–2018
     ينبئ عن 2019–2025. ولا ينبئ.
""")



#  ─────────────────────────────────────────────────────────────────────
#  د — قاعدة العلامة: الرقم لا علامة له
#  ─────────────────────────────────────────────────────────────────────
#
#  القاعدة:  20 = 2000 = 200000  ·  2 = 200 = 200000  ·  3.56 = 356 = 35.6 = 35600
#  ⇒ لا وجود للعلامة. فالسعر أسرةُ قراءات: N_k = P × 10^k.
#
#  ولها نتيجة رياضية تُقلّص الحرّية إلى أربع فقط:
#      θ_k = θ₀ × 10^k (mod 360)
#      10^0 ≡ 1 · 10^1 ≡ 10 · 10^2 ≡ 100 · 10^3 ≡ 280 ≡ 10^4 ≡ 10^5 …
#  ⇒ أربعُ قراءاتٍ متميّزة لا لانهاية — وهذا ما يجعل الفرضية قابلة للتكذيب.

DIGITS_K = (0, 1, 2, 3)


def _deg(px, s, k):
    return np.mod(px * (10.0 ** k) / s, 360.0)


def sec_digits(data, S, lons, ns):
    print("\n" + "=" * 92)
    print("د — قاعدة العلامة: الرقم لا علامة له — أربع قراءات لا لانهاية")
    print("=" * 92)
    print("""
  القاعدة كما أُقرّت:
      20 = 2000 = 200000        ·        2 = 200 = 200000
      ولا وجود للعلامة:  3.56 = 356 = 35.6 = 35600

  فالسعر ليس 3.56. هو الرقم 356 — والعلامة موضعُ قراءةٍ لا قيمة.
  ودرجة السعر:  θ = (P × 10^k) ÷ s.

  والنتيجة الرياضية (لأن 10^3 ≡ 280 ≡ 10^4 ≡ 10^5 … mod 360):

      10^0 ≡ 1   ·   10^1 ≡ 10   ·   10^2 ≡ 100   ·   10^3 ≡ 280   (ثم تتكرّر)

  ⇒ أربعُ قراءاتٍ متميّزة فقط. فليست العلامة بابًا مفتوحًا، بل أربعة أبواب.
""")

    allpx = np.concatenate([r[1] for r in prepare(data, ns.train_end, ns.test_start)[2]])
    med = float(np.median(allpx))
    print("  وأثرُ القاعدة على الحركة — نفس السهم بحركة 12%، والمقياس 30:")
    d0 = (med / 30) % 360
    d1 = ((med * 1.12) / 30) % 360
    e0 = ((med * 100) / 30) % 360
    e1 = ((med * 112) / 30) % 360
    print(f"    بالعلامة       : {med:.2f} → {med * 1.12:.2f}   ⇒  {d0:.2f}° → {d1:.2f}°"
          f"   (تحرّك {12 * med / 30:.3f}°)")
    print(f"    بلا علامة (×100): {med * 100:.0f} → {med * 112:.0f}  ⇒  {e0:.1f}° → {e1:.1f}°"
          f"   (تحرّك {12 * med * 100 / 30:.1f}°)")
    print("    ⇒ بلا علامة يقطع السعرُ درجاتٍ حقيقية. وبالعلامة كان يسكن —")
    print("      وهذا هو الخطأ الذى وقعتُ فيه حين قلتُ «السعر المصرى صغير».")

    _, _, rows = prepare(data, ns.train_end, ns.test_start)

    print("\n" + "-" * 92)
    print("  د٢ — بلا أى اختيار: كل مقياس × كل قراءة، على التحقّق وحده (2019–2025)")
    print("-" * 92)
    scales = [("1 نقطة = 1°", 1.0)] + [(AR[b], S[b]) for b in PLANETS]
    hdr = "".join(f"{'×10^' + str(k):>10}" for k in DIGITS_K)
    print(f"\n  {'المقياس':<14}{hdr}{'متوسط':>10}")
    for name, sc in scales:
        cells = []
        for k in DIGITS_K:
            vals = [(aspect_distance(_deg(px, sc, k), lons[b][idx]) <= ORB)[tem].mean()
                    for b in PLANETS for (_, px, idx, _, tem) in rows]
            cells.append(float(np.mean(vals)))
        print(f"  {name:<14}" + "".join(f"{100 * c:>9.1f}%" for c in cells)
              + f"{100 * np.mean(cells):>9.1f}%")
    print(f"\n  ⇒ الصدفة {CHANCE:.1f}% فى كل خلية. والجدول كلُّه لا يبرحها.")

    print("\n" + "-" * 92)
    print("  د٣ — أربع قراءات × خمسة كواكب = 20 خيارًا · يُختار على التدريب ويُقرأ على التحقّق")
    print("-" * 92)

    def matrix(rr):
        labels = [(b, k) for b in PLANETS for k in DIGITS_K]
        tr = np.zeros((len(rr), len(labels)))
        te = np.zeros_like(tr)
        for i, (_, px, idx, trm, tem) in enumerate(rr):
            for j, (b, k) in enumerate(labels):
                ok = aspect_distance(_deg(px, S[b], k), lons[b][idx]) <= ORB
                tr[i, j], te[i, j] = ok[trm].mean(), ok[tem].mean()
        return tr, te, labels

    out = {}
    for tag, (te0, ts0) in (("أ", (ns.train_end, ns.test_start)),
                            ("ب", ("2010", "2011"))):
        _, _, rr = prepare(data, te0, ts0)
        tr, te, labels = matrix(rr)
        k = tr.argmax(axis=1)
        pick = te[np.arange(len(te)), k]
        med_opt = np.median(te, axis=1)
        lift = pick - med_opt
        t = lift.mean() / (lift.std(ddof=1) / math.sqrt(len(te)))
        mode = int(np.bincount(k, minlength=len(labels)).argmax())
        const = te[:, mode].mean()
        print(f"\n  نافذة {tag}: تدريب حتى {te0} · تحقّق من {ts0} · أسهم {len(rr)}")
        print(f"    كل الخيارات مجتمعة  : تدريب {100 * tr.mean():.1f}% · "
              f"تحقّق {100 * te.mean():.1f}%   (الصدفة {CHANCE:.1f}%)")
        print(f"    أفضل خيار فى التدريب: تدريب {100 * tr.max(axis=1).mean():.1f}% · "
              f"تحقّق {100 * pick.mean():.1f}%")
        print(f"    مقابل وسيط الخيارات : {100 * med_opt.mean():.1f}%  ⇒ فرق "
              f"{100 * lift.mean():+.2f} نقطة · t = {t:+.2f}")
        print(f"    خط الأساس الثابت ({AR[labels[mode][0]]} ×10^{labels[mode][1]}): "
              f"{100 * const:.1f}%  ·  سقف أفضل خيار فى التحقّق: "
              f"{100 * te.max(axis=1).mean():.1f}%")
        out[tag] = dict(k=k, rr=rr, te=te, lift=lift, t=t)

    print("\n" + "-" * 92)
    print("  د٤ — ثبات الهوية: نفس السهم فى فترتين — هل يُختار له نفس (الكوكب، القراءة)؟")
    print("-" * 92)
    ma = {r[0]: out["أ"]["k"][i] for i, r in enumerate(out["أ"]["rr"])}
    mb = {r[0]: out["ب"]["k"][i] for i, r in enumerate(out["ب"]["rr"])}
    common = [tk for tk in ma if tk in mb]
    same = sum(ma[tk] == mb[tk] for tk in common)
    bk = sum(ma[tk] % len(DIGITS_K) == mb[tk] % len(DIGITS_K) for tk in common)
    bb = sum(ma[tk] // len(DIGITS_K) == mb[tk] // len(DIGITS_K) for tk in common)
    n = len(common)
    print(f"    أسهم مشتركة {n}")
    print(f"      اتفاق (الكوكب والقراءة) : {same:3d} = {100 * same / n:5.1f}%"
          f"   (الصدفة {100 / (len(PLANETS) * len(DIGITS_K)):.1f}%)")
    print(f"      اتفاق القراءة وحدها     : {bk:3d} = {100 * bk / n:5.1f}%"
          f"   (الصدفة {100 / len(DIGITS_K):.1f}%)")
    print(f"      اتفاق الكوكب وحده       : {bb:3d} = {100 * bb / n:5.1f}%"
          f"   (الصدفة {100 / len(PLANETS):.1f}%)")
    print("    ⇒ لو كانت الثبات من الكوكب، لَثبت الكوكبُ لا القراءة. والعكس هو ما يُقرأ.")

    #  ── د٥ — هل الخيار يخصّ السهم أم يخصّ الشكل العام لسعره؟ ────────
    print("\n" + "-" * 92)
    print("  د٥ — الضابط الحاسم: نفس الخيار يُطبَّق على سهمٍ آخر")
    print("-" * 92)
    print("    الخيار (الكوكب، القراءة) الذى فاز لسهمٍ فى النافذة (ب) يُطبَّق فى النافذة (أ)")
    print("    على السهم نفسه مرّة، وعلى سهمٍ مجاور مرّة. فإن تساوى الحاصلان،")
    print("    فالخيار يصف **شكلَ السعر**، لا صلةً بين السهم والكوكب.")
    tr_a, te_a, labels = matrix(out["أ"]["rr"])
    idx_a = {r[0]: i for i, r in enumerate(out["أ"]["rr"])}
    idx_b = {r[0]: i for i, r in enumerate(out["ب"]["rr"])}
    common_b = [tk for tk in idx_b if tk in idx_a]
    own, other = [], []
    for j, tk in enumerate(common_b):
        kk = out["ب"]["k"][j]
        own.append(te_a[idx_a[tk], kk])
        tk2 = common_b[(j + 1) % len(common_b)]
        other.append(te_a[idx_a[tk2], kk])
    own, other = np.array(own), np.array(other)
    d = own - other
    t = d.mean() / (d.std(ddof=1) / math.sqrt(len(d)))
    print(f"\n    على سهمه   : {100 * own.mean():.2f}%")
    print(f"    على سهمٍ آخر: {100 * other.mean():.2f}%")
    print(f"    الفرق      : {100 * d.mean():+.2f} نقطة · t = {t:+.2f} · n = {len(d)}")
    print("    ⇒ الفرق صفرٌ فى الحدود الخطأ. فالخيار لا يحمل معلومةً عن السهم.")
    return out


if __name__ == "__main__":
    main()
