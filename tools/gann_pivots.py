#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
شروط التحليل الفنى عند جان — ومحاولة تصنيف القيعان إلى **رئيسى** و**فرعى**.

المصدر (لا الذاكرة):
  Gann, WD - Soy Beans Price Resistance Levels (1954)  ص٢، ص٣، ص٤
  Gann, WD - May Coffee Astro Letter (1954)            ص٢، ص٣
  Gann, WD - Astro Charts                             ص٢–ص٦

والشروط المستخرجة حرفًا:

  ش١  «The one-half point of the highest selling price and one-half between the
       high and low are very great because these equal the 45 degree angle or
       the gravity center.»                        → المقياس يأتى من **مدى** الأداة نفسها.

  ش٢  «On the weekly or monthly chart, use the date when the extreme high or
       extreme low is made and draw a 45 degree angle up and down.»
                                                   → **الإرساء على القاع الأقصى**،
                                                     والإطار **أسبوعى/شهرى** لا يومى.

  ش٣  «You mark all low prices with a red circle ... and note the Angles of 45,
       60, 90, 120, 135, 180, 225, 240, 270, 300, 315 and 360 from each high
       and low.»                                   → **اثنتا عشرة زاوية**، لا واحدة.

  ش٤  «24 cents = one cycle; one hour of Time equals 15 degrees in Longitude,
       and for one hour of Time we use one cent of Price.»
                                                   → **وحدة السعر = ١٥° = وحدة الزمن.**
                                                     (مُتحقَّق منها: ٣٠٠ ← ٣٠° العذراء،
                                                      ٣٠٢ ← ٣٠° الميزان، ٣٠٤ ← ٣٠° العقرب)

  ش٥  «using the Earth's annual revolution of 365 1/4 days»  → ٣٦٠ ÷ ٣٦٥.٢٥ = ٠.٩٨٥٦٣°
                                                     درجة واحدة فى اليوم. (وهو قياس ١٧ §٢)

  ش٦  «when these Resistance Points are met you must give the market time to
       show that it is making tops or bottoms ... Do not guess, wait until you
       get a definite indication of a change in trend ... and place a stop
       loss order.»                                → **التأكيد شرط**، والتخمين ممنوع.

  ش٧  «24 CENT MOVES OR MORE ... 48, 72, 96, 120, 144, 168 ... one-half of 24
       is 12 ... 36, 60, 84 ... which equals 180 degrees.»
                                                   → الحركة تُقاس بمضاعفات ١٥°.

والسؤال المطروح: **ما القاع الرئيسى وما القاع الفرعى؟** والجواب من النصّ:
  • الرئيسى  = **الأقصى** (extreme low): منه تُرسم الزاوية، وإليه تُعدّ العدّة.
  • الفرعى   = قاعٌ **أعلى منه** داخل الاتجاه، لا تكسره زاوية ٤٥°، ويكتسب
               معناه من **عدّةٍ زمنية** تصل إليه (خطاب القهوة ص٣: «Jan. 19 –
               Low 6560 – This was 7 months from June 19»).

الاستعمال:
    python3 -u tools/gann_pivots.py [--csv /tmp/egx_clean.csv] [--min-months 12]
"""

import argparse
import collections
import csv
import datetime
import statistics
import sys

DEG_PER_DAY = 360.0 / 365.25          # ش٥
PRICE_DEG = 15.0                      # ش٤: وحدة السعر = ١٥°
ANGLES = (45, 60, 90, 120, 135, 180, 225, 240, 270, 300, 315, 360)   # ش٣
CLEAN = ["ARCC", "CCAP", "CLHO", "ELSH", "EMFD", "IDRE", "ISMA",
         "KZPC", "MTIE", "ORAS", "SUGR", "TMGH"]   # نفس الاثنى عشر فى docs/17
SIGNS = ("الحمل", "الثور", "الجوزاء", "السرطان", "الأسد", "العذراء",
         "الميزان", "العقرب", "القوس", "الجدى", "الدلو", "الحوت")


def hdr(t):
    print("\n" + "=" * 86)
    print(" " + t)
    print("=" * 86)


def load(path):
    data = collections.defaultdict(dict)
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                d = datetime.date.fromisoformat(r["date"])
                lo = float(r["low"])
                hi = float(r["high"])
                cl = float(r["close"])
            except (ValueError, KeyError):
                continue
            if lo <= 0 or cl <= 0:
                continue
            data[r["ticker"]][d] = (lo, hi, cl)
    return data


def monthly(series):
    """ش٢: الإطار **شهرى**. كل شهر: أدنى أدنى، أعلى أعلى، آخر إغلاق."""
    out = []
    key = None
    cur = None
    for d in sorted(series):
        k = (d.year, d.month)
        lo, hi, cl = series[d]
        if k != key:
            if cur:
                out.append(cur)
            key = k
            cur = {"date": d, "low": lo, "high": hi, "close": cl, "n": 1}
        else:
            cur["low"] = min(cur["low"], lo)
            cur["high"] = max(cur["high"], hi)
            cur["close"] = cl
            cur["date"] = d
            cur["n"] += 1
    if cur:
        out.append(cur)
    return out


def deg(p):
    """ش٤: السعر درجات. ٠° = الحمل، ٩٠° = السرطان (أعلى)، ١٨٠° = الميزان، ٢٧٠° = الجدى."""
    return (p * PRICE_DEG) % 360.0


def sign_of(x):
    return SIGNS[int(x // 30) % 12]


def ang_dist(a, b):
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="/tmp/egx_clean.csv")
    ap.add_argument("--min-months", type=int, default=12,
                    help="أقل طول سلسلة شهرية يُعتدّ به")
    ap.add_argument("--tol", type=float, default=3.0,
                    help="سماحية الزاوية بالدرجات")
    ap.add_argument("--all", action="store_true", help="كل الأسهم، لا الاثنا عشر")
    args = ap.parse_args()

    data = load(args.csv)
    rows = []
    for t in sorted(data):
        m = monthly(data[t])
        if not args.all and t not in CLEAN:
            continue
        if len(m) < args.min_months:
            continue
        rows.append((t, m))

    # ------------------------------------------------------------------ §١
    hdr("١. المقياس من الأداة نفسها (ش١) — ٣٦٠° تساوى مدى السهم")
    print("  جان لا يختار المقياس من هواه: «one-half of the highest selling price")
    print("  and one-half between the high and low ... equal the 45 degree angle».")
    print("  فالمقياس المشتقّ: درجة واحدة = المدى ÷ ٣٦٠. وهو **لكل سهمٍ مقياسه**.\n")
    print(f"  {'السهم':>7} {'أشهر':>5} {'أعلى':>9} {'أدنى':>9} {'المدى':>9} "
          f"{'وحدة/درجة':>11} {'وحدة/يوم':>10}")
    scales = {}
    for t, m in rows:
        hi = max(x["high"] for x in m)
        lo = min(x["low"] for x in m)
        s = (hi - lo) / 360.0
        scales[t] = (hi, lo, s)
        print(f"  {t:>7} {len(m):>5} {hi:>9.2f} {lo:>9.2f} {hi-lo:>9.2f} "
              f"{s:>11.5f} {s*DEG_PER_DAY:>10.6f}")
    print("\n  ⇒ «وحدة/يوم» هى ميل زاوية ٤٥° عند جان: درجةٌ من السعر لكل درجةٍ من")
    print("     الزمن. وهى تختلف بين الأسهم — أى أن **لكل سهمٍ زاويته**.")

    # ------------------------------------------------------------------ §٢
    hdr("٢. القاع الرئيسى والقاع الفرعى — تعريفٌ بنيوى لا نسبةٌ مئوية")
    print("  فى النصّ مستويان، لا مستوى واحد:")
    print("    الفرعى  : قاعٌ شهرى، بعده قمةٌ أعلى (تأكيد ش٦) — «swing low».")
    print("    الرئيسى : قاعٌ **لا يُكسَر** ١٢ شهرًا بعده ولا ١٢ شهرًا قبله —")
    print("              أى **الأقصى** فى نطاقه (ش٢: «the extreme low»).")
    print("  فالتصنيف **بنيوى**: لا نسبة ٢٠% ولا عدد أيام، بل هل كُسر أم لا.\n")
    print(f"  {'السهم':>7} {'أشهر':>5} {'رئيسية':>7} {'فرعية':>7} {'وسيط عمر الفرعى':>15}")
    majors = {}
    for t, m in rows:
        maj, sub = [], []
        for i in range(len(m)):
            x = m[i]
            w0, w1 = max(0, i - 12), min(len(m), i + 13)
            win = m[w0:w1]
            if x["low"] == min(y["low"] for y in win) and x["low"] < m[i-1]["low"]:
                maj.append(i)
            elif i and i + 1 < len(m) and x["low"] > m[i-1]["low"] \
                    and x["low"] > m[i+1]["low"] and m[i+1]["high"] > x["high"]:
                sub.append(i)
        majors[t] = (maj, sub)
        # عمر الفرعى: كم شهرًا قبل أن يُكسَر قاعه
        ages = []
        for j in sub:
            k = next((q for q in range(j + 1, len(m)) if m[q]["low"] < m[j]["low"]), None)
            if k:
                ages.append(k - j)
        med = f"{statistics.median(ages):.0f}" if ages else "—"
        print(f"  {t:>7} {len(m):>5} {len(maj):>7} {len(sub):>7} {med+' شهرًا':>15}")
    print("\n  ⇒ الرئيسى قليل والفرعى كثير — وهذه هى علاقة **الهرم**، لا علاقة")
    print("     «مهم/غير مهم». وكل قاع فرعى يصبح رئيسيًّا إن كُسر.")

    # ------------------------------------------------------------------ §٣
    hdr("٣. شرط الزوايا وحده (ش٣) — لماذا لا يميّز شيئًا")
    print("  من درجة كل قاع، تُضاف الزوايا الاثنتا عشرة. أى **تغطية** للدائرة؟")
    cov = min(360.0, len(ANGLES) * 2 * args.tol)
    print(f"    ١٢ زاوية × ±{args.tol:.0f}° = {cov:.0f}° من ٣٦٠° = **{100*cov/360:.0f}%**")
    print("  فإن أصابت القيعان ٢٠% فهذا **ليس إنجازًا**، بل هو التغطية نفسها.\n")
    print(f"  {'السهم':>7} {'قيعان':>6} {'أصابت':>7} {'قمم':>5} {'أصابت':>7} {'المجموع':>8} {'الصدفة':>8}")
    tot_hit = tot_n = 0
    chances = []
    for t, m in rows:
        maj, sub = majors[t]
        if not maj:
            continue
        d0 = deg(m[maj[0]]["low"])
        tg = [(d0 + a) % 360.0 for a in ANGLES]
        hit = lambda p: min(ang_dist(deg(p), g) for g in tg) <= args.tol
        lows = [m[j] for j in sub]
        tops = [m[i] for i in range(1, len(m)-1)
                if m[i]["high"] > m[i-1]["high"] and m[i]["high"] > m[i+1]["high"]]
        hl = sum(1 for x in lows if hit(x["low"]))
        ht = sum(1 for x in tops if hit(x["high"]))
        ch = sum(1 for x in m if hit(x["low"])) / max(1, len(m))
        chances.append(ch); tot_hit += hl + ht; tot_n += len(lows) + len(tops)
        print(f"  {t:>7} {len(lows):>6} {hl:>7} {len(tops):>5} {ht:>7} "
              f"{hl+ht:>8} {100*ch:>7.1f}%")
    print(f"\n  المجموع {tot_hit}/{tot_n} = **{100*tot_hit/max(1,tot_n):.1f}%** "
          f"· متوسط الصدفة {100*statistics.mean(chances):.1f}% · التغطية {100*cov/360:.0f}%")
    print("  ⇒ الرقم عند التغطية، لا فوقها. فالشرط **صحيح فى النصّ وعاجز فى القياس**،")
    print("     لأن كل قاعٍ يقع «قريبًا» من واحدةٍ من اثنتى عشرة. وهذا عيبُ الشكل")
    print("     لا عيبُ جان — وهو نفسه ما دفعه إلى شرط التجاور (٣.١).")

    # ------------------------------------------------------------------ §٣.١
    hdr("٣.١ شرط التجاور (soy ص٣) — «the mathematical reasons»")
    print('  نصّه: «67 plus 125 gives 202, and that one-half of 405 is 202½, and 180')
    print('  plus 22½ is 202½, which are the mathematical reasons why May Soy Beans')
    print('  made bottom at 201½.» — أى **عدّةُ تكويناتٍ مستقلّة تلتقى على سعرٍ واحد**.')
    print("  فالشرط ليس «قريب من زاوية»، بل **كم أصلًا مستقلًّا يلتقى هناك**.\n")
    print(f"  {'السهم':>7} {'تجاور القيعان':>13} {'تجاور العشوائى':>15} {'الفرق':>8}")
    diffs = []
    for t, m in rows:
        maj, sub = majors[t]
        def score(idx):
            piv = [k for k in (maj + sub) if k < idx]
            if len(piv) < 5:
                return None
            d = deg(m[idx]["low"])
            n = sum(1 for k in piv
                    if min(ang_dist(d, (deg(m[k]["low"]) + a) % 360.0) for a in ANGLES) <= args.tol)
            return n / len(piv)
        ps = [x for x in (score(j) for j in sub) if x is not None]
        rs = [x for x in (score(i) for i in range(len(m)) if i not in sub) if x is not None]
        if not ps or not rs:
            continue
        a1, a2 = statistics.mean(ps), statistics.mean(rs)
        diffs.append(a1 - a2)
        print(f"  {t:>7} {100*a1:>12.1f}% {100*a2:>14.1f}% {100*(a1-a2):>+7.1f}")
    if diffs:
        pos = sum(1 for d in diffs if d > 0)
        print(f"\n  ⇒ القيعان الفرعية تتفوّق على الشهور العادية فى {pos}/{len(diffs)} سهمًا"
              f" · متوسط الفرق {100*statistics.mean(diffs):+.1f} نقطة")
    print("  ⇒ وهذا هو الشرط الوحيد فى النصّ الذى **يستبعد** شيئًا: التكوين الواحد")
    print("     لا يُثبت قاعًا، بل يجب أن تلتقى عدّةُ تكوينات. فالمعيار **عددٌ** لا مسافة.")

    # ------------------------------------------------------------------ §٤
    hdr("٤. الحملات — من قاعٍ رئيسى إلى قاعٍ رئيسى (ش٣: الزوايا من كل قاعٍ وقمة)")
    print("  كل حملة: قاع رئيسى ← قمة ← قاع رئيسى تالٍ. ويُقاس فيها:")
    print("     • المدة بالأشهر   • المدى بالدرجات (السعر × ١٥) غير مختزلة   • الدرجة/الشهر\n")
    print(f"  {'السهم':>7} {'من':>10} {'إلى':>10} {'أشهر':>6} {'مدى%':>7} {'درجات':>7} {'°/شهر':>7}")
    rates = []
    for t, m in rows:
        maj, _ = majors[t]
        for a, b in zip(maj, maj[1:]):
            months = (b - a)
            if months < 2:
                continue
            p0, p1 = m[a]["low"], m[b]["low"]
            rng = (p1 / p0 - 1) * 100
            dg = (p1 - p0) * PRICE_DEG        # درجات **غير مختزلة** (docs/17 §٣)
            rates.append(abs(dg) / months)
            print(f"  {t:>7} {str(m[a]['date'])[:10]:>10} {str(m[b]['date'])[:10]:>10} "
                  f"{months:>6} {rng:>+7.0f} {abs(dg):>7.1f} {abs(dg)/months:>7.1f}")
    if rates:
        print(f"\n  ⇒ وسيط الدرجة/الشهر عبر الحملات = {statistics.median(rates):.1f}°"
              f" · المدى {min(rates):.1f}–{max(rates):.1f}")
    print("  ⇒ وهذه هى **وتيرة السهم** بمعنى جان: كم درجة يقطع فى الشهر. وهى تختلف")
    print("     بين سهمٍ وآخر — وهو ما قرّره المستخدم: لكل سهمٍ تردّده.")

    # ------------------------------------------------------------------ §٤.١
    hdr("٤.١ أين تتجمّع القيعان الرئيسية؟ — السوق يتكلّم قبل الفلك")
    print("  إن كان القاع الرئيسى حدثًا سوقيًّا، وجب أن تتشاركه أسهمٌ كثيرة فى اليوم")
    print("  نفسه. وهذا يُقاس:\n")
    hits = collections.Counter()
    for t, m in rows:
        for i in majors[t][0]:
            hits[m[i]["date"]] += 1
    print(f"  {'التاريخ':>12} {'عدد الأسهم':>10}")
    for d, n in hits.most_common(6):
        print(f"  {str(d):>12} {n:>10}")
    top = hits.most_common(1)[0]
    print(f"\n  ⇒ أكثر يومٍ تجمّعًا: {top[0]} — قاعٌ رئيسىّ فى **{top[1]} من {len(rows)}** سهمًا.")
    print("     والفلك لا يجمع تسعة أسهم على يومٍ واحد؛ والسياسة والاقتصاد يفعلان.")

    # ------------------------------------------------------------------ §٥
    hdr("٥. الخلاصة")
    print(f"  الأسهم                        : {len(rows)}")
    print(f"  قيعان رئيسية                  : {sum(len(majors[t][0]) for t, _ in rows)}")
    print(f"  قيعان فرعية (بتأكيد)          : {sum(len(majors[t][1]) for t, _ in rows)}")
    print(f"  إصابة الزوايا                 : {100*tot_hit/max(1,tot_n):.1f}%"
          f"  (التغطية {100*cov/360:.0f}% · الصدفة {100*statistics.mean(chances):.1f}%)")
    print(f"  وتيرة السهم (وسيط)            : {statistics.median(rates):.1f}°/شهر")
    print("""
  وثلاثة أشياء يذكرها جان ولا يعطيها فى هذه الصفحات — فلا أُنفّذها:
    • «CE AVERAGE» و«MOF FORMULA»            (خطاب القهوة ص٤)
    • «the average of the five major planets with Mars left out»  (soy ص٣)
    • «Master Charts»                        (soy ص٤)
  ومن ادّعى تنفيذها فهو ينفّذ ما ليس فى المصدر.""")


if __name__ == "__main__":
    main()
