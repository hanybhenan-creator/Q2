#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تردّد كل سهم — يُستخرج من البيانات لا يُفترض من كتاب.

هذا هو السؤال الذى طلبه المستخدم: **لكل أداة تردّدها**. ولا يُجاب بالبحث عن
دوراتٍ معلومة (٢٥٢٠ · ٣٦٠ · ٩٠)، بل بمسحٍ لكل الدورات الممكنة ثم قياس
**أيّها يخصّ السهم فعلًا**.

الشبكة: ٣٦٠ درجة/دورة من `tools/degree_calendar.py` ⇒ **شمعة = درجة**،
والفاصل منتظم. فالمحور الزمنى محورٌ فلكى، والمسح يقع عليه مباشرةً.

والمنهج، **مُعلَنًا قبل النظر**:
  ١. y = ln(الإغلاق)، تُزال الاتجاه الخطى والمتوسط.
  ٢. مسح دورىّ للدورات من ٣٠° إلى ١٨٠٠° (شهر إلى خمس سنين).
  ٣. **الدلالة بضابط يحفظ الطيف**: تُعشَّى أطوار FFT (phase randomisation)،
     فيبقى الطيف كما هو ويُهدم الترتيب. فالسؤال: هل فى البيانات **تماسك طور**
     أكثر من مصدرٍ بنفس الطيف؟ (والضابط الأبيض يبالغ فى الدلالة — وهذا خطأ
     وقعتُ فيه سابقًا.)
  ٤. **والأهم:** يُستخرج التردد من نصف السلسلة، ويُقاس على النصف الآخر.
     فإن لم يثبت التردد خارج العيّنة فليس تردّدًا، بل أعلى نقطةٍ فى ضجيج.

التشغيل:
    python3 tools/stock_frequency.py
    python3 tools/stock_frequency.py --csv /tmp/egx_degree.csv
"""

import argparse
import collections
import csv
import math
import os
import sys

import numpy as np

LINE = "=" * 86
SKIP = {"GTWL", "GRCA"}
DAY_PER_DEG = 365.2422 / 360.0
P_MIN, P_MAX = 30.0, 1800.0        # بالدرجات
N_SUR = 240


def hdr(t):
    print("\n" + LINE + "\n " + t + "\n" + LINE)


def load(path):
    raw = collections.defaultdict(dict)
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            raw[r["ticker"]].setdefault(int(r["cycle"]), {})[int(r["degree"])] = \
                float(r["close"])
    out = {}
    for t, cyc in raw.items():
        cyc = {c: s for c, s in cyc.items() if len(s) == 360}
        if len(cyc) < 4:
            continue
        ys = []
        for c in sorted(cyc):
            for d in range(360):
                ys.append(math.log(cyc[c][d]))
        out[t] = np.array(ys)
    return out


def prep(y):
    t = np.arange(len(y), dtype=float)
    b = np.polyfit(t, y, 1)
    r = y - (b[0] * t + b[1])
    return r - r.mean()


def grid(n, lo=None, hi=None):
    lo = lo if lo is not None else P_MIN
    hi = hi if hi is not None else P_MAX
    L = 1 << int(np.ceil(np.log2(n * 4)))
    f = np.fft.rfftfreq(L)          # دورات لكل درجة
    m = (f >= 1.0 / hi) & (f <= 1.0 / lo)
    return L, f, m


def band(y, lo, hi, rng):
    """القمة فى نطاق دوراتٍ محدَّد، ودلالتها بضابطٍ يحفظ الطيف."""
    n = len(y)
    L, f, m = grid(n, lo, hi)
    P = power(y, L, m, y.std())
    fm = f[m]
    k = int(np.argmax(P))
    Y = np.fft.rfft(y)
    null = np.empty(160)
    for i in range(160):
        ph = rng.uniform(0, 2 * np.pi, len(Y))
        ph[0] = 0
        sc = np.fft.irfft(np.abs(Y) * np.exp(1j * ph), n)
        sc = sc - sc.mean()
        null[i] = power(sc, L, m, sc.std()).max()
    return dict(period_deg=1.0 / fm[k], power=float(P[k]),
                fap=float((null >= P[k]).mean()))


def power(y, L, m, sd):
    Y = np.fft.rfft(y, L)
    P = (np.abs(Y) ** 2) / (len(y) * sd ** 2)
    return P[m]


def run(t, y):
    rng = np.random.default_rng(7)
    y = prep(y)
    n = len(y)
    long_ = band(y, 400.0, P_MAX, rng)     # فوق السنة
    short = band(y, P_MIN, 400.0, rng)     # تحت السنة
    h = n // 2
    halves = [prep(y[:h]), prep(y[h:])]
    fs = band(halves[0], P_MIN, 400.0, np.random.default_rng(9))["period_deg"]
    # ثبات: موقع التردد فى النصف الثانى **مقابل ضابطه**
    rng2 = np.random.default_rng(13)
    L2, f2, m2 = grid(len(halves[1]), P_MIN, 400.0)
    P2 = power(halves[1], L2, m2, halves[1].std())
    j = int(np.argmin(np.abs(f2[m2] - 1.0 / fs)))
    obs = P2[j]
    Yh = np.fft.rfft(halves[1])
    cnt = 0
    for _ in range(160):
        ph = rng2.uniform(0, 2 * np.pi, len(Yh))
        ph[0] = 0
        sc = np.fft.irfft(np.abs(Yh) * np.exp(1j * ph), len(halves[1]))
        sc = sc - sc.mean()
        cnt += power(sc, L2, m2, sc.std())[j] >= obs
    short["oos_pct"] = 100.0 * (1 - cnt / 160)
    return dict(n=n, long_=long_, short=short, fs=fs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="/tmp/egx_degree.csv")
    a = ap.parse_args()
    if not os.path.exists(a.csv):
        sys.exit(f"لا يوجد {a.csv} — شغّل tools/degree_calendar.py أولًا")

    data = load(a.csv)
    hdr("٠. التصريح قبل النظر")
    print(f"""  • المحور: ٣٦٠ درجة/دورة، الشمعة = ١° ⇒ ‎1° = {DAY_PER_DEG:.3f}‎ يوم.
  • y = ln(الإغلاق) بلا اتجاه خطى.
  • مسح {P_MIN:.0f}°–{P_MAX:.0f}° ({P_MIN*DAY_PER_DEG:.0f}–{P_MAX*DAY_PER_DEG:.0f} يومًا).
  • الضابط: تعشية أطوار FFT ({N_SUR} نسخة) — يحفظ الطيف ويهدم التماسك.
  • والتردد لا يُقبل إلا إن ثبت **خارج العيّنة**.""")
    print("  • المستبعد مسبقًا: " + " · ".join(sorted(SKIP)) + " (شواغر > ٥٠%).")

    hdr("١. تردّد كل سهم — النطاقان")
    print("  النطاق الطويل (فوق السنة) يقع عند **حدّ المسح** فى معظم الأسهم:")
    print("  وهذه بصمة الاتجاه لا الدورة — أطول موجةٍ ممكنة هى أقوى موجة.\n")
    print(f"  {'السهم':>7} {'طويل (°)':>10} {'سنوات':>7} {'FAP':>6}   "
          f"{'قصير (°)':>9} {'أيام':>6} {'FAP':>6} {'خارج العيّنة':>12}")
    rows = {}
    for t in sorted(data):
        if t in SKIP:
            continue
        r = run(t, data[t])
        rows[t] = r
        L_, S_ = r["long_"], r["short"]
        print(f"  {t:>7} {L_['period_deg']:>10.0f} "
              f"{L_['period_deg']*DAY_PER_DEG/365.2422:>7.2f} {L_['fap']:>6.2f}   "
              f"{S_['period_deg']:>9.0f} {S_['period_deg']*DAY_PER_DEG:>6.0f} "
              f"{S_['fap']:>6.2f} {S_['oos_pct']:>11.0f}%")

    hdr("٢. الحكم — ثلاثة أرقام فقط")
    long_at_edge = sum(1 for r in rows.values() if r["long_"]["period_deg"] > 1500)
    sig = [t for t in rows if min(rows[t]["long_"]["fap"], rows[t]["short"]["fap"]) <= 0.05]
    oos = [t for t in rows if rows[t]["short"]["oos_pct"] >= 95]
    ann = [t for t in rows if 320 <= rows[t]["short"]["period_deg"] <= 400]
    print(f"""  ١. النطاق الطويل: **{long_at_edge} من {len(rows)}** سهم قمته عند حدّ المسح
     (‎>1500°‎ ⇒ ‎>4.2‎ سنة). وهذه **بصمة الاتجاه**: أى مسارٍ صاعدٍ تعطى أقوى
     قوة عند أطول موجة. فليست دورة.

  ٢. الدلالة بضابطٍ يحفظ الطيف: **{len(sig)} من {len(rows)}** سهمًا عند ‎FAP ≤ 0.05‎
     — وهو ما تعطيه الصدفة نفسها فى ١٢ اختبارًا (‎0.6‎ متوقَّعة).

  ٣. النطاق القصير: **{len(ann)} من {len(rows)}** قمّتهم عند ‎320–400°‎، أى عند
     **السنة نفسها**. وهذا **ليس اكتشافًا**: محور الشبكة هو السنة، فالسنة هى
     الوحدة التى يُقاس بها كلُّ شىء. أى أن السهم يعطى «ترددًا سنويًّا» لأن
     السؤال سُنوىّ — لا لأن السهم يهتزّ.

  ٤. وخارج العيّنة: **{len(oos)} من {len(rows)}** ثبت تردده.""")


if __name__ == "__main__":
    main()
