#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تقويم السهم — كشف ميكانيكى للقمم والقيعان، واختبار هل له دورية.

ثلاثة أسئلة، ولكل سؤال ضابط عدم مستقل:

1. **التزامن:** هل تقع انعطافات الأسهم فى التواريخ نفسها أكثر من الصدفة؟
   الضابط: إزاحة دورية عشوائية لكل سهم (تحفظ بنية السهم وتكسر المحاذاة).

2. **الدورية:** هل فى سلسلة السهم قمة طيفية تتجاوز ما ينتجه **ضجيج أحمر**
   (AR(1) بنفس معامل الارتباط والانحراف)؟ الضابط ليس خلطًا عشوائيًا —
   فالخلط يشوّه الطيف ويجعل كل المقارنات تبدو إيجابية.

3. **طول الدورة:** هل تتجمع الأطوال بين الأسهم أم تتناثر؟

الانعطاف يُعرَّف ميكانيكيًا: ارتداد بنسبة r عن أقصى (أو أدنى) نقطة، مع
تجاهل أول 30 صفًا (كقاعدة Bry–Boschan). والعتبة تُجرَّب على خمس قيم
فتصير اختبار حساسية لا اختيارًا.

الاستعمال:
    python3 tools/egx_calendar.py --csv /tmp/egx_clean.csv --since 2014-01-01
"""

import argparse
import collections
import datetime
import math
import statistics

import numpy as np


def load(csv_path, since, min_rows):
    by = collections.defaultdict(list)
    with open(csv_path, encoding="utf-8") as fh:
        import csv as _csv
        for r in _csv.DictReader(fh):
            if r["date"] < since:
                continue
            try:
                c = float(r["close"])
            except ValueError:
                continue
            if c > 0:
                by[r["ticker"]].append((r["date"], c))
    out = {}
    for t, v in by.items():
        v.sort()
        # كل ما يبدأ بـ EGX مؤشر سوق لا سهم — يستبعد وإلا دخل الزمر كطرف.
        if len(v) >= min_rows and not t.upper().startswith("EGX"):
            out[t] = v
    return out


def zigzag(prices, thresh, skip=30):
    """مؤشرات الانعطاف (قمم وقيعان متبادلة) بنسبة ارتداد thresh."""
    k = prices[skip:]
    piv, trend = [], 0
    if len(k) < 10:
        return piv
    hi = lo = k[0]
    hi_i = lo_i = 0
    started = False
    for i, p in enumerate(k):
        if not started:
            hi = lo = p
            hi_i = lo_i = i
            started = True
            continue
        if trend >= 0:
            if p > hi:
                hi, hi_i = p, i
            elif p <= hi * (1 - thresh):
                if trend > 0 or not piv:
                    piv.append(hi_i)
                trend = -1
                lo, lo_i = p, i
        if trend <= 0:
            if p < lo:
                lo, lo_i = p, i
            elif p >= lo * (1 + thresh):
                if trend < 0:
                    piv.append(lo_i)
                trend = +1
                hi, hi_i = p, i
    return piv


def residual_series(dates, prices, returns, market):
    """المسار الخاص بالسهم بعد إزالة عامل السوق (بيتا)."""
    pairs = [(returns[d], market[d]) for d in returns if d in market]
    if len(pairs) < 300:
        return None
    mx = statistics.mean(p[1] for p in pairs)
    my = statistics.mean(p[0] for p in pairs)
    cov = sum((p[1] - mx) * (p[0] - my) for p in pairs)
    var = sum((p[1] - mx) ** 2 for p in pairs)
    beta = cov / var if var else 1.0
    cum, ser = 0.0, {}
    for i, d in enumerate(dates):
        if i > 0 and d in returns and d in market:
            cum += returns[d] - beta * market[d]
        ser[d] = math.exp(cum)
    return ser


def peak_sharpness(x, lo=30, hi=750):
    n = len(x)
    if n < 400:
        return None
    x = x - x.mean()
    f = np.abs(np.fft.rfft(x * np.hanning(n))) ** 2
    fr = np.fft.rfftfreq(n)
    ok = (fr > 1 / hi) & (fr < 1 / lo)
    if not ok.any():
        return None
    p = f[ok]
    return p.max() / p.mean()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--since", default="2014-01-01")
    ap.add_argument("--min-rows", type=int, default=1000)
    ap.add_argument("--trials", type=int, default=150)
    ns = ap.parse_args()

    keep = load(ns.csv, ns.since, ns.min_rows)
    print(f"الأسهم: {len(keep)}   |   منذ {ns.since}")

    # ── ١) الانعطافات وحساسية العتبة
    print("\n" + "=" * 70)
    print("  ١) الانعطافات الميكانيكية — حساسية العتبة")
    print("=" * 70)
    for th in (0.05, 0.10, 0.15, 0.20, 0.30):
        tot, lens = 0, []
        for t, v in keep.items():
            pv = zigzag([p for _, p in v], th)
            tot += len(pv)
            lens += [b - a for a, b in zip(pv, pv[1:]) if 20 <= b - a <= 1500]
        med = statistics.median(lens) if lens else 0
        cv = (statistics.pstdev(lens) / statistics.mean(lens)) if lens else 0
        print(f"  عتبة {th:>5.0%}:  انعطافات {tot:>7,}  ·  وسيط الطور {med:>5.0f} يومًا  ·  معامل الاختلاف {cv:.3f}")

    # ── ٢) التزامن
    print("\n" + "=" * 70)
    print("  ٢) التزامن بين الأسهم — والضابط: إزاحة دورية لكل سهم")
    print("=" * 70)
    for th in (0.20,):
        for label, use_resid in (("السعر الخام", False), ("بعد إزالة السوق", True)):
            pivs, idx = {}, {}
            if use_resid:
                rets = {}
                for t, v in keep.items():
                    r = {}
                    ds = [d for d, _ in v]
                    for a, b in zip(ds, ds[1:]):
                        da = datetime.date.fromisoformat(a)
                        db = datetime.date.fromisoformat(b)
                        if (db - da).days <= 10:
                            r[b] = math.log(dict(v)[b] / dict(v)[a])
                    rets[t] = r
                mk = collections.defaultdict(list)
                for t in rets:
                    for d, r in rets[t].items():
                        mk[d].append(r)
                market = {d: statistics.median(v) for d, v in mk.items() if len(v) >= 30}
            for t, v in keep.items():
                ds = [d for d, _ in v]
                if use_resid:
                    ser = residual_series(ds, [p for _, p in v], rets[t], market)
                    if ser is None:
                        continue
                    vals = [ser[d] for d in ds]
                else:
                    vals = [p for _, p in v]
                pv = zigzag(vals, th)
                if len(pv) >= 3:
                    pivs[t] = [ds[i + 30] for i in pv]
                    idx[t] = ds
            if not pivs:
                continue
            cnt = collections.Counter()
            for t, ps in pivs.items():
                for d in ps:
                    cnt[d] += 1
            real_ss = sum(x * x for x in cnt.values())
            real_max = max(cnt.values())
            rng = np.random.default_rng(7)
            sss, mxs = [], []
            for _ in range(ns.trials):
                c = collections.Counter()
                for t, ps in pivs.items():
                    seq = idx[t]
                    pos = {d: i for i, d in enumerate(seq)}
                    off = int(rng.integers(0, len(seq)))
                    for d in ps:
                        c[seq[(pos[d] + off) % len(seq)]] += 1
                sss.append(sum(x * x for x in c.values()))
                mxs.append(max(c.values()))
            p_ss = (sum(1 for s in sss if s >= real_ss) + 1) / (ns.trials + 1)
            print(f"\n  [{label}] {sum(len(p) for p in pivs.values()):,} انعطافًا على {len(pivs)} سهمًا")
            print(f"     أعلى تكدّس يوم: {real_max:>4}  |  عدم {statistics.mean(mxs):>5.1f}  →  ×{real_max/statistics.mean(mxs):.2f}")
            print(f"     مجموع المربعات: {real_ss:>8,}  |  عدم {statistics.mean(sss):>8,.0f}  →  ×{real_ss/statistics.mean(sss):.2f}   (p={p_ss:.3f})")
            print(f"     أكثر 5 تواريخ: {[f'{d}({c})' for d, c in cnt.most_common(5)]}")

    # ── ٣) الدورية ضد ضجيج أحمر
    print("\n" + "=" * 70)
    print("  ٣) هل للدورية وجود يتجاوز الضجيج الأحمر؟ (AR(1))")
    print("=" * 70)
    rng = np.random.default_rng(31)
    R, N = [], []
    for t, v in keep.items():
        lr = np.diff(np.log(np.array([p for _, p in v])))
        if len(lr) < 400:
            continue
        s = peak_sharpness(lr)
        if s is None:
            continue
        mu, sd = lr.mean(), lr.std()
        rho = float(np.corrcoef(lr[:-1], lr[1:])[0, 1])
        rho = max(min(rho, 0.999), -0.999)
        e = rng.normal(0, sd * math.sqrt(1 - rho * rho), len(lr))
        sim = np.empty(len(lr))
        sim[0] = rng.normal(0, sd)
        for i in range(1, len(lr)):
            sim[i] = rho * sim[i - 1] + e[i]
        s2 = peak_sharpness(sim + mu)
        if s2 is not None:
            R.append(s)
            N.append(s2)
    R, N = np.array(R), np.array(N)
    thr = np.percentile(N, 95)
    print(f"  الأسهم: {len(R)}")
    print(f"  سُمك القمة (أقصى/متوسط القدرة):")
    print(f"     حقيقى  وسيط {np.median(R):5.2f}  ·  رباعيات {np.percentile(R,25):.2f}/{np.percentile(R,75):.2f}")
    print(f"     AR(1)  وسيط {np.median(N):5.2f}  ·  رباعيات {np.percentile(N,25):.2f}/{np.percentile(N,75):.2f}")
    print(f"     النسبة {np.median(R)/np.median(N):.2f}×")
    print(f"  عتبة 95% من العدم {thr:.2f} → يعبرها {(R>thr).sum()} من {len(R)} ({100*(R>thr).mean():.1f}%)  [المتوقع 5%]")


if __name__ == "__main__":
    main()
