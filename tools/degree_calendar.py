#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الشمعة الفلكية — تعبئة أيام العطل بيوميّاتٍ تحمل الزمن.

المبدأ الذى طلبه المستخدم:
    القدماء عدّوا بالأيام، والكون لا ينتظم بالليل والنهار؛ انتظامه بالدرجة
    الفلكية. فالشبكة ليست أيام التقويم، بل **درجات الشمس**.

فبناءً عليه، لا تُبنى الشبكة على «٣٦٥ يومًا» ولا على «٣٦٠ يومًا» تقويميًّا،
بل على **٣٦٠ درجة من الطول السماوى الظاهرى للشمس**، صفرُها **الاعتدال الربيعى**
(٠° الحمل). فكل شمعة = درجة واحدة بالضبط، ولا كسور.

    • كل جلسة تُنسب إلى درجة الشمس يومها (٠–٣٥٩).
    • الدرجة التى فيها جلسات: شمعة حقيقية (O=أول افتتاح · H=أعلى · L=أدنى ·
      C=آخر إغلاق).
    • الدرجة الخالية (عطلة/إجازة/توقف): شمعة اصطناعية تحمل **متوسط آخر شمعة
      حقيقية على OHLC** — أى (O+H+L+C)/4 — بالغًا ما بلغ نوع التوقف.
    • فتصير كل دورةٍ فلكية **٣٦٠ شمعة**، كلُّ شمعةٍ درجةٌ، وكلُّ درجةٍ زمن.

التشغيل:
    python3 tools/degree_calendar.py                      # الأسهم النظيفة
    python3 tools/degree_calendar.py --all                # كل السوق
    python3 tools/degree_calendar.py --csv /tmp/egx_clean.csv --out /tmp/egx_degree.csv
"""

import argparse
import collections
import csv
import datetime as dt
import math
import os
import sys

try:
    import swisseph as swe
except ImportError:
    sys.exit("يحتاج pyswisseph:  pip install --break-system-packages --user pyswisseph")

LINE = "=" * 84
CLEAN = ["GTWL", "TMGH", "GRCA", "IDRE", "ISMA", "CCAP", "EMFD", "CLHO",
         "ORAS", "SUGR", "ELSH", "ARCC", "MTIE", "KZPC"]


def hdr(t):
    print("\n" + LINE + "\n " + t + "\n" + LINE)


swe.set_ephe_path(None)


def sun_lon(d):
    """الطول السماوى الظاهرى للشمس، ٠–٣٦٠، عند ١٢:٠٠ UT من اليوم."""
    jd = swe.julday(d.year, d.month, d.day, 12.0)
    x, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)
    return x[0] % 360.0


_EQ = {}


def equinox_jd(y):
    """اعتدال مارس للعام y (نقطة الصفر)."""
    if y not in _EQ:
        _EQ[y] = swe.solcross_ut(0.0, swe.julday(y, 1, 1, 0.0))
    return _EQ[y]


def cycle_of(d):
    """رقم الدورة الشمسية: الدورة تبدأ عند اعتدال مارس."""
    jd = swe.julday(d.year, d.month, d.day, 12.0)
    return d.year if jd >= equinox_jd(d.year) else d.year - 1


def load(path, tickers=None):
    series = collections.defaultdict(list)
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        for r in csv.DictReader(f):
            t = r["ticker"]
            if tickers and t not in tickers:
                continue
            try:
                d = dt.datetime.strptime(r["date"][:10], "%Y-%m-%d").date()
                o, h, l, c = (float(r["open"]), float(r["high"]),
                              float(r["low"]), float(r["close"]))
            except (ValueError, KeyError):
                continue
            if min(o, h, l, c) <= 0:
                continue
            series[t].append((d, o, h, l, c))
    for t in series:
        series[t].sort()
    return series


def build(rows):
    """٣٦٠ درجة لكل دورة، والشواغر تُملأ بمتوسط آخر شمعة."""
    by_deg = collections.defaultdict(list)     # (cycle, deg) -> [(d,o,h,l,c)]
    for d, o, h, l, c in rows:
        by_deg[(cycle_of(d), int(sun_lon(d)))].append((d, o, h, l, c))

    cycles = sorted({k[0] for k in by_deg})
    out = []
    for cy in cycles:
        real = {}
        for deg in range(360):
            cell = by_deg.get((cy, deg))
            if cell:
                o = cell[0][1]
                h = max(x[2] for x in cell)
                l = min(x[3] for x in cell)
                c = cell[-1][4]
                real[deg] = (1, len(cell), cell[0][0], cell[-1][0],
                             o, h, l, c, (o + h + l + c) / 4.0)
        if not real:
            continue
        # الشواغر قبل أوّل شمعة حقيقية تُملأ منها، وما بعدها يُملأ بالمتوسط الجارى
        first = real[min(real)]
        carry = first[8]
        for deg in range(360):
            if deg in real:
                s = real[deg]
                carry = s[8]
            else:
                s = (0, 0, None, None, carry, carry, carry, carry, carry)
            out.append((cy, deg) + s)
    return out, cycles


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="/tmp/egx_clean.csv")
    ap.add_argument("--out", default="/tmp/egx_degree.csv")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--ticker", default=None)
    a = ap.parse_args()

    if not os.path.exists(a.csv):
        sys.exit(f"لا يوجد {a.csv} — شغّل tools/egx_load.py أولًا")

    tickers = None
    if a.ticker:
        tickers = {a.ticker}
    elif not a.all:
        tickers = set(CLEAN)

    hdr("٠. الشبكة — لماذا ٣٦٠ درجة لا ٣٦٥ يومًا؟")
    print("  صفر الشبكة = **الاعتدال الربيعى** (٠° الحمل)، والدرجة = **الطول السماوى")
    print("  الظاهرى للشمس** عند منتصف نهار الجلسة (١٢:٠٠ UT).\n")
    eq = equinox_jd(2020)
    print(f"  {'التاريخ':>12} {'درجة الشمس':>12} {'0.98565×الأيام':>16} {'الفرق':>9}")
    for d in (dt.date(2020, 4, 15), dt.date(2020, 7, 1),
              dt.date(2020, 10, 1), dt.date(2020, 12, 21)):
        L = sun_lon(d)
        naive = (0.98565 * (swe.julday(d.year, d.month, d.day, 12.0) - eq)) % 360
        print(f"  {d.isoformat():>12} {L:>11.3f}° {naive:>15.3f}° {L-naive:>+8.3f}°")
    print("""
  ⇒ الفرق يبلغ **‎−3.8°‎** فى أوائل أكتوبر، ويبلغ ‎−2.3°‎ عند الانقلاب الشتوى:
     عدُّ الأيام يقول ‎272.4°‎ والصواب ‎270.1°‎. أى أن **حوالى أربع درجات** —
     ودرجةٌ واحدة شمعة. فمن عدّ الأيام لم يعدّ الدرجة.

  ⇒ وهذا هو معنى «الكون لا ينتظم بالليل والنهار»: التقويم عدٌّ منتظم، والأرض
     لا تدور منتظمة على مدارها. والدرجة تأخذ الشذوذ المدارى، والأيام لا تأخذه.

  ⇒ والمكسب العملى: كل شمعة = **١°** بالضبط، فالمحور الزمنى والمحور الفلكى
     محورٌ واحد — وهذا هو الربط بين السعر والزمن.""")

    series = load(a.csv, tickers)
    hdr("١. البناء — ٣٦٠ شمعة لكل دورة، والشواغر اصطناعية")
    print(f"  {'السهم':>7} {'دورات':>6} {'شمعة':>7} {'حقيقية':>8} {'اصطناعية':>9} "
          f"{'نسبة العطل':>10}")
    total_rows = 0
    detail = {}
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "cycle", "degree", "real", "n_days",
                    "first_date", "last_date", "open", "high", "low", "close"])
        for t in sorted(series):
            rows = series[t]
            if len(rows) < 400:
                continue
            slots, cycles = build(rows)
            if not slots:
                continue
            real = sum(s[2] for s in slots)
            n = len(slots)
            detail[t] = (len(cycles), n, real, n - real, (n - real) / n)
            total_rows += n
            print(f"  {t:>7} {len(cycles):>6} {n:>7} {real:>8} {n-real:>9} "
                  f"{100*(n-real)/n:>9.1f}%")
            for s in slots:
                w.writerow([t, s[0], s[1], s[2], s[3],
                            s[4].isoformat() if s[4] else "",
                            s[5].isoformat() if s[5] else "",
                            f"{s[6]:.4f}", f"{s[7]:.4f}", f"{s[8]:.4f}", f"{s[9]:.4f}"])

    print(f"\n  كُتب **{total_rows:,}** صفًّا إلى `{a.out}`")

    hdr("٢. التحقّق — الشواغر صُنعت بالوصفة المطلوبة")
    t = next(iter(detail))
    slots, _ = build(series[t])
    bad = synth = 0
    shown = 0
    print(f"  عيّنة من {t} (اصطناعى = متوسط آخر شمعة حقيقية على OHLC):")
    print(f"  {'درجة':>5} {'حقيقى':>6} {'O':>9} {'H':>9} {'L':>9} {'C':>9}")
    by_cyc = collections.defaultdict(list)
    for s_ in slots:
        by_cyc[s_[0]].append(s_)
    lead = 0
    for cy in sorted(by_cyc):
        block = by_cyc[cy]
        first_real = next((x[10] for x in block if x[2] == 1), None)
        prev_mean = first_real          # شواغر أوّل الدورة تُملأ من أوّل شمعة
        for s_ in block:
            if s_[2] == 1:
                prev_mean = s_[10]
                continue
            synth += 1
            if first_real is not None and abs(s_[6] - first_real) < 1e-6 and \
                    block.index(s_) < block.index(next(x for x in block if x[2] == 1)):
                lead += 1
            ok = prev_mean is not None and abs(s_[6] - prev_mean) < 1e-6
            bad += not ok
            if shown < 5 and s_[1] > 20:
                print(f"  {s_[1]:>5} {'لا':>6} {s_[6]:>9.4f} {s_[7]:>9.4f} {s_[8]:>9.4f} "
                      f"{s_[9]:>9.4f}   = متوسط الشمعة السابقة "
                      f"({'✔' if ok else '✘'})")
                shown += 1
    print(f"\n  فحص **كل** الشواغر فى {t}: {synth} شمعة اصطناعية · {bad} مخالفة "
          f"(منها {lead} فى مقدّمة الدورة تُملأ من أوّل شمعة، إذ لا «سابقة» لها).")

    per_cycle = collections.Counter(s_[0] for s_ in slots)
    full = [cy for cy, n in per_cycle.items() if n == 360]
    print(f"  دورات {t}: {len(per_cycle)} — كاملة (٣٦٠): **{len(full)}** — "
          f"ناقصة: {len(per_cycle)-len(full)}")

    heavy = [(k, v) for k, v in detail.items() if v[4] > 0.50]
    if heavy:
        print("\n  **تنبيه جودة:** أسهم أكثر من نصف درجاتها اصطناعية "
              "(فراغاتها أطول من ١٨٠ يومًا):")
        for k, v in sorted(heavy, key=lambda x: -x[1][4]):
            print(f"     {k}: {100*v[4]:.0f}% اصطناعى — كلُّ قياسٍ عليها مشكوك")

    print(f"""
  ⇒ الدرجة الخالية تحمل **متوسط آخر شمعة حقيقية** — لا إغلاقها، ولا متوسطًا
     عامًّا. فالسعر لا يتحرّك فى العطلة، لكن **الزمن يتحرّك**؛ والشبكة تحفظ
     الاثنين: الزمن بالدرجة، والسعر بمتوسطٍ ثابتٍ لا يُنشئ حركةً كاذبة.

  ⇒ وكلُّ دورة كاملة = **٣٦٠ صفًّا بالضبط**، بلا استثناء. ونسبة الشواغر
     ‎{100*detail[t][4]:.0f}%‎ — وهى **أيام العطل والإجازات والتوقّف كلها**، بأى
     نوعٍ كانت، لأنها كلها درجاتٌ لا جلسات.""")

    hdr("٣. ماذا يترتّب على هذه الشبكة")
    print("""  ١. المحور الأفقى صار **درجة لا يومًا**: ٠° اعتدال ربيعى، ٩٠° انقلاب
     صيفى، ١٨٠° اعتدال خريفى، ٢٧٠° انقلاب شتوى. وهى النقاط الكاردينالية
     بعينها التى ذكرها المستخدم.
  ٢. **٠ = ١٨٠** فى المستوى: كلاهما خطُّ الصفر فى الموجة، والأول صاعد
     والثانى هابط. فالمستوى لا يكفى للحكم على موضع الدورة — يُضاف إليه
     **إشارة السرعة** (مشتقة المنحنى). وهذا محور `tools/degree_cycle.py`.
  ٣. ٩٠° = القمة · ٢٧٠° = القاع، **إن كان** للسعر موجةٌ بهذا الطور. أما إن
     لم تكن، فالشبكة تبقى صحيحة، والدعوى تسقط — وهذا ما يُختبر لا يُفترض.""")


if __name__ == "__main__":
    main()
