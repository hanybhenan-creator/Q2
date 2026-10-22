#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نبض السهم — مشتقًّا من أربع مسلَّمات، لا من كتاب.

المسلَّمات (من المستخدم، وهى التى تُبنى عليها الأداة):
  أ١. العلامة العشرية لا تفرّق:  123 = 12.3 = 1.23  ⇒ الأرقام أصناف لا نقاط.
  أ٢. الجذر يجمع الصور:  √12 = √1200 = √120000   ⇒ الصورة = تكافؤ أس العشرة.
  أ٣. الأرقام تمشى فى صورة فردية وزوجية ⇒ غطاء مزدوج على الدائرة.
  أ٤. الرقم لا يُعرف إلا بالكلمة التالية ⇒ الموضع وحده مبهم، والاستمرار يرفع الإبهام.

والنتائج التى تفرضها هذه المسلَّمات — بالبرهان لا بالاختيار:

  (١) من أ١: أى دالة مشروعة للرقم هى دالة على مَانتِيسَّاه فى [1,10). والخريطة
      الوحيدة الطبيعية على هذا الخارج هى الزاوية:
          φ(x) = 360 · log10(x)        [درجة]
      لأن log10(10^k·x) = log10(x) + k ⇒ φ تُزاح بثابت، والزاوية باقية.

  (٢) من أ٢ وأ٣: √ على الدائرة نصفُ الزاوية:  φ(√x) = φ(x)/2 (mod 180).
      فهى دالة 2-إلى-1، ونواتها {0°,180°} — وهى بالضبط «الصورتان».
      ⇒ الفردى/الزوجى ليس وصفًا، بل **البِتّ الذى يفقده الجذر**.

  (٣) من أ٤: البِتّ المفقود لا يأتى من الرقم، بل من **الكلمة التالية** — أى من
      الاستمرار. فرفع الإبهام (unwrapping) هو الأثر الرياضى للمسلَّمة الرابعة.

  (٤) ومعادلة الحركة: φ نقطة على دائرة، فسرعة الزاوية ω = dφ/dt هى الشكل
      الوحيد **غير المتغير** تحت المضاعفة (§14.1: d(x·k)=d(x)+ثابت ⇒ ω لا يتغير).
      ⇒ «معدل الاهتزاز» عند جان = ω، بالدرجة/يوم. وهو السبب الرياضى الذى يجعل
      التجزئة لا تهم.

  (٥) و«النبض» = زمن دورة كاملة (360°)، أى الزمن اللازم ليُضاعف السعر عشر مرات.
      والخطوة 45° = ×10^(1/8) = ×1.334 — وهى أقرب خطوة قابلة للقياس فى 12 سنة.

الاختبار: هل خطوات السهم بين انعطافين **مكمَّاة** بمضاعفات 45° (أو 30°/90°)؟
وهذا هو الاختبار الوحيد لزوايا جان القابل للتكذيب، لأن فرق الزاويتين لا يتأثر
بأى مضاعفة للسعر — بخلاف الدرجة المطلقة (§14.8).

الضابط: الأيام العادية نفسها، بنفس توزيع الفواصل الزمنية — فلو كانت الانعطافات
مكمَّاة لظهر التركيز فيها وحدها.

التشغيل:
    python3 tools/egx_pulse.py --csv /tmp/egx_clean.csv
"""

import argparse
import collections
import csv
import math

import numpy as np

STEPS = (30.0, 45.0, 90.0, 120.0)


def load(path, since, min_rows):
    by = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["date"] < since:
                continue
            try:
                c = float(r["close"])
            except ValueError:
                continue
            if c > 0:
                by[r["ticker"]][r["date"]] = c
    return {t: v for t, v in by.items()
            if not t.upper().startswith("EGX") and len(v) >= min_rows}


def zigzag(prices, th=0.20, skip=30):
    p = prices[skip:]
    if len(p) < 10:
        return []
    out, trend = [], 0
    hi = lo = p[0]
    hi_i = lo_i = 0
    for i, x in enumerate(p):
        if trend >= 0:
            if x > hi:
                hi, hi_i = x, i
            elif x <= hi * (1 - th):
                if trend > 0 or not out:
                    out.append(hi_i)
                trend, lo, lo_i = -1, x, i
        if trend <= 0:
            if x < lo:
                lo, lo_i = x, i
            elif x >= lo * (1 + th):
                if trend < 0:
                    out.append(lo_i)
                trend, hi, hi_i = 1, x, i
    return out


def rayleigh(angles_deg, period):
    """اختبار انتظام دائرى: هل تتكدّس الزوايا عند مضاعفات period؟"""
    th = np.asarray(angles_deg) * (2 * math.pi / period)
    n = len(th)
    if n < 20:
        return None
    R = abs(np.exp(1j * th).mean())
    p = math.exp(-n * R * R) if R > 0 else 1.0
    return n, R, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--since", default="2014-01-01")
    ap.add_argument("--min-rows", type=int, default=1000)
    ap.add_argument("--threshold", type=float, default=0.20)
    ap.add_argument("--shuffles", type=int, default=300)
    ns = ap.parse_args()

    data = load(ns.csv, ns.since, ns.min_rows)
    print(f"أسهم: {len(data)}")

    piv_dphi, piv_dt, rates, plain = [], [], [], []
    for t, v in data.items():
        ds = sorted(v)
        p = np.array([v[d] for d in ds])
        phi = 360.0 * np.log10(p)
        idx = zigzag(p, ns.threshold)
        pos = [i + 30 for i in idx]
        for a, b in zip(pos, pos[1:]):
            if b - a < 5:
                continue
            d = phi[b] - phi[a]
            piv_dphi.append(d)
            piv_dt.append(b - a)
            rates.append(abs(d) / (b - a))
        # ضابط: خطوات عادية بنفس الفواصل الزمنية
        rng = np.random.default_rng(3)
        for a, b in zip(pos, pos[1:]):
            if b - a < 5:
                continue
            a2 = int(rng.integers(0, len(phi) - (b - a)))
            plain.append(phi[a2 + (b - a)] - phi[a2])

    piv_dphi = np.array(piv_dphi)
    plain = np.array(plain)
    rates = np.array(rates)
    print(f"انعطافات متتالية: {len(piv_dphi):,} · ضابط: {len(plain):,}")
    print(f"متوسط خطوة الانعطاف |Δφ| = {np.median(np.abs(piv_dphi)):.1f}° "
          f"· وسيط الزمن {np.median(piv_dt):.0f} يومًا")
    print(f"سرعة الزاوية ω (وسيط): {np.median(rates):.2f}°/يوم "
          f"= دورة كاملة كل {360 / np.median(rates):.0f} يومًا")

    # الضابط الصحيح: نفس الإجراء على مسار عشوائى بنفس التقلب.
    # لأن عتبة 20% تفرض حدًّا أدنى على الخطوة (360·log10(1.2)=28.5°)، فأى
    # تكدّس عند مضاعفات الزوايا قد يكون أثر العتبة لا أثر الهندسة.
    rng = np.random.default_rng(11)
    gbm = []
    for t, v in data.items():
        ds = sorted(v)
        p_ = np.array([v[d] for d in ds])
        r = np.diff(np.log(p_))
        walk = p_[0] * np.exp(np.concatenate([[0.0], np.cumsum(
            rng.normal(r.mean(), r.std(), len(r)))]))
        idx = zigzag(walk, ns.threshold)
        pos = [i + 30 for i in idx]
        for a, b in zip(pos, pos[1:]):
            if b - a >= 5:
                gbm.append(360.0 * (math.log10(walk[b]) - math.log10(walk[a])))
    gbm = np.array(gbm)

    print("\n═══ هل الخطوات مكمَّاة بمضاعفات الزوايا؟ (اختبار رايلى) ═══")
    print("   (R يقيس التكدّس: 0 = منتظم · 1 = كل الخطوات على المضاعف)")
    for st in STEPS:
        r1 = rayleigh(piv_dphi, st)
        r0 = rayleigh(plain, st)
        r2 = rayleigh(gbm, st)
        if r1 and r0 and r2:
            print(f"  مضاعفات {st:5.0f}°:  حقيقى R = {r1[1]:.3f}"
                  f"  |  مسار عشوائى بنفس العتبة R = {r2[1]:.3f}"
                  f"  |  أيام عادية R = {r0[1]:.3f}")
    print(f"  (المسار العشوائى: {len(gbm):,} خطوة)")

    print("\n═══ النبض: هل للأسهم أصناف سرعة، أم تدرّج؟ ═══")
    per = collections.defaultdict(list)
    for t, v in data.items():
        ds = sorted(v)
        p_ = np.array([v[d] for d in ds])
        phi = 360.0 * np.log10(p_)
        idx = zigzag(p_, ns.threshold)
        pos = [i + 30 for i in idx]
        for a, b in zip(pos, pos[1:]):
            if b - a >= 20:
                per[t].append(abs(phi[b] - phi[a]) / (b - a))
    med = {t: float(np.median(x)) for t, x in per.items() if len(x) >= 4}
    vals = np.array(list(med.values()))
    pulse = 360.0 / vals
    print(f"  أسهم: {len(med)} · وسيط ω {np.median(vals):.2f}°/يوم"
          f" · وسيط النبض {np.median(pulse):.0f} يومًا للدورة الكاملة")
    print(f"  النبض: ربعيات {np.percentile(pulse, 25):.0f}/"
          f"{np.percentile(pulse, 75):.0f} · المدى {pulse.min():.0f}–{pulse.max():.0f}")
    print(f"  معامل الاختلاف بين الأسهم {vals.std() / vals.mean():.2f} — تدرّج")
    within = [np.std(x) / np.mean(x) for x in per.values() if len(x) >= 4]
    print(f"  والتشتت داخل السهم الواحد {np.median(within):.2f}"
          f"  (أقل من 1 = نبض يثبت داخل السهم)")

    print("\n═══ الصورتان: هل يبقى السهم فى تكافؤ أس العشرة؟ ═══")
    same = tot = 0
    for t, v in data.items():
        ds = sorted(v)
        p_ = np.array([v[d] for d in ds])
        idx = zigzag(p_, ns.threshold)
        pos = [i + 30 for i in idx]
        for a, b in zip(pos, pos[1:]):
            ea = int(math.floor(math.log10(p_[a])))
            eb = int(math.floor(math.log10(p_[b])))
            tot += 1
            same += ((ea % 2) == (eb % 2))
    print(f"  خطوات تبقى فى الصورة نفسها: {100 * same / tot:.1f}% من {tot:,}")
    print("  (الصورة تتغير عند عبور ×10 — والقراءة تحتاج تاريخًا طويلًا للحكم)")


if __name__ == "__main__":
    main()
