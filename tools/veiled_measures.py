#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
القياسات المستورة — نحوُ كتاب ١٦٦٧ «Times of the Bible».

المصدر: النسخة الإنجليزية الأصلية (٧٨ ص، إعادة طبع «Gann Study Group»)
        docs/sources/times-of-the-bible-1667-en.txt

قاعدة الكتاب واحدة، ويصرّح بها فى ص٤٤:
    «as they may allude to signall Hours ... so they may be Days, and Years also»
أى أن **العدد لا يُعرف إلا بوحدته**، والوحدة تُعطى بالكلمة التالية. والكتاب
يفعل ذلك لا يقول به فقط: يُكرّر العدد نفسه فى أذرعٍ وأشبارٍ وأصابعٍ وأغلوةٍ
وساعاتٍ وأيامٍ وسنين.

ويُخرج هذا الملف خمسة أشياء:
  ١. **أقفال الاقتباس**: كلُّ نقلٍ يُتحقَّق آليًّا من وجوده فى صفحته، وإلا سقط.
  ٢. **جرد الوحدات**: الوحدات التى يستعملها الكتاب، مَعْدودةً من نصّه.
  ٣. **تقويم الكتاب نفسه**: ٣٦٠ يومًا · ٣٠ يومًا · ٢٤ ساعة — محسوبًا من عباراته.
  ٤. **اختبار «التوافق»** بضابط مُطابِق: هل أعداد الكتاب تسبح فى وحداتٍ أكثر من
     أعدادٍ فى مثل تكرارها؟ وهل ذلك يُثبت شيئًا عن النصّ أم عن المؤلف؟
  ٥. **النحو على خطاب جان والسعر**: تعيين الوحدة، وأثره على الدرجة.

التشغيل:
    python3 tools/veiled_measures.py
"""

import collections
import os
import re
import statistics
import sys

SRC = "docs/sources/times-of-the-bible-1667-en.txt"
LINE = "=" * 82


def hdr(t):
    print("\n" + LINE + "\n " + t + "\n" + LINE)


def norm(t):
    return " ".join(t.split())


# ─────────────────────────────────────────────────────────────────────
# ٠. أقفال الاقتباس — لا نقلَ بلا تحقّق
# ─────────────────────────────────────────────────────────────────────

QUOTES = [
    (3, "Noahs Ark was built in 120 years and there were 120 hours before Adams day"),
    (3, "120 Trumpets, for the Temple"),
    (8, "1600 Furlongs: or Years"),
    (8, "144 hours of the Week brought up the Sabbath Day"),
    (8, "7000 cubits, in the circuit of the stories of Noahs Ark"),
    (12, "the first Sabbath day began at 144 hours"),
    (44, "so they may be Days, and Years also"),
    (44, "1335 is but 45 more than 1290"),
    (45, "if these also be for years, they will end between 1666, and 1675"),
    (47, "And the Ark was tossed by the Flood, 3600 hours, or 150 days"),
    (48, "There are just 3600 days, in 10 years of 360 days; or 12 moneths of 30 days"),
    (54, "2520 more, the dayes of 7 years, come out at 1665, or 1666"),
    (56, "the Sanctuary should be fully cleansed in 2300 days"),
]


def load():
    if not os.path.exists(SRC):
        sys.exit(f"missing {SRC}")
    s = open(SRC, encoding="utf-8").read()
    parts = re.split(r"===== PAGE (\d+) =====", s)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts), 2)}


def locks(pages):
    hdr("٠. أقفال الاقتباس — كلُّ نقلٍ يُتحقَّق من صفحته آليًّا")
    ok = bad = 0
    for p, q in QUOTES:
        body = norm(pages.get(p, ""))
        good = norm(q) in body
        ok += good
        bad += not good
        print(f"  {'✔' if good else '✘'} ص{p:<3} {q[:74]}")
    print(f"\n  {ok} قفلًا صحيحًا من {ok+bad}.")
    if bad:
        print("  ⇒ إقتباسٌ لم يوجد فى صفحته: يُسحب من كل مستند قبل النشر.")
    print("""
  ⇒ لماذا هذا أولًا: كان النصّ الذى بين يدىَّ سابقًا **ترجمة آلية مقلوبة**،
     فلم يكن ممكنًا نقلُ حرفٍ واحد. والآن النصّ الإنجليزى الأصلى بين يدىَّ،
     فصار كل نقلٍ قابلًا للتحقّق — وكلُّ نقلٍ لا يمرّ بهذا القفل يُسحب.""")


# ─────────────────────────────────────────────────────────────────────
# ١. جرد الوحدات
# ─────────────────────────────────────────────────────────────────────

UNITS = (r"(cubits?|shekels?|talents?|furlongs?|dayes|days?|years?|hours?|weeks?"
         r"|moneths?|months?|chapters?|verses?|letters?|digits?|spans?|boards?"
         r"|trumpets?|inches?|miles?|stadia)")
FIX = {"dayes": "day", "days": "day", "moneths": "month", "months": "month",
       "inches": "inch", "stadia": "furlong"}
PAT = re.compile(r"(\d[\d,]*)\s+" + UNITS, re.I)


def inventory(pages):
    hdr("١. جرد الوحدات — مَعْدودة من نصّ الكتاب")
    pairs, per_num, page_of = set(), collections.defaultdict(set), collections.defaultdict(set)
    for p, b in pages.items():
        for m in PAT.finditer(b):
            n = int(m.group(1).replace(",", ""))
            u = m.group(2).lower()
            u = FIX.get(u, u[:-1] if u.endswith("s") else u)
            pairs.add((n, u))
            per_num[n].add(u)
            page_of[n].add(p)
    units = sorted({u for _, u in pairs})
    print(f"  أزواج (عدد + وحدة): {len(pairs)} · أعداد مختلفة: {len(per_num)} "
          f"· وحدات: {len(units)}\n")
    print("  الوحدات: " + " · ".join(units) + "\n")
    print(f"  {'العدد':>6} {'صفحات':>6} {'وحدات':>6}  الوحدات")
    for n in sorted(per_num, key=lambda x: (-len(per_num[x]), x))[:12]:
        print(f"  {n:>6} {len(page_of[n]):>6} {len(per_num[n]):>6}  "
              + " · ".join(sorted(per_num[n])))
    return per_num, page_of


# ─────────────────────────────────────────────────────────────────────
# ٢. تقويم الكتاب نفسه
# ─────────────────────────────────────────────────────────────────────

def calendar():
    hdr("٢. تقويم الكتاب — مأخوذ من عباراته، لا من خارجها")
    rows = [
        ("٣٦٠٠ ساعة = ١٥٠ يومًا", 3600, 24, 150, "ص٤٧، ٥٤"),
        ("١٥٠ يومًا = ٥ أشهر", 150, 30, 5, "ص٤٨ (١٢ شهرًا × ٣٠)"),
        ("١٤٤ ساعة = ٦ أيام", 144, 24, 6, "ص١٢، ٣٦"),
        ("٢٥٢٠ يومًا = ٧ سنين", 2520, 7, 360, "ص٥٤"),
        ("٣٦٠٠ يوم = ١٠ سنين", 3600, 10, 360, "ص٤٨"),
    ]
    print(f"  {'العبارة':26} {'المقسوم':>9} {'المقسوم عليه':>13} {'الناتج':>7} {'صحيح؟':>7}")
    for label, a, b, want, pg in rows:
        got = a / b
        print(f"  {label:26} {a:>9} {b:>13} {got:>7.0f} "
              f"{'✔' if abs(got-want) < 1e-9 else '✘':>7}   {pg}")
    print("""
  ⇒ النتيجة البنيوية: **السنة عند صاحب ١٦٦٧ = ٣٦٠ يومًا، والشهر = ٣٠ يومًا،
     واليوم = ٢٤ ساعة.** ونصُّه صريح: «There are just 3600 days, in 10 years of
     360 days; or 12 moneths of 30 days apiece».

  ⇒ **وهذه هى سنة دانيال النبوية نفسها** (٣٦٠ يومًا) ودائرة جان نفسها (٣٦٠ درجة).
     فالثلاثة — ١٦٦٧ ودانيال وجان — يقفون على تقويمٍ واحد. وهذا ليس ربطًا
     رمزيًّا: هو حسابٌ من عبارات الكتاب ومن تك ٧–٨ (١٥٠ يومًا بين ١٧/٢ و١٧/٧).

  ⇒ ويُصحَّح بهذا: ما قلتُه سابقًا إن الكتاب «يُصرّح» بأن ٧٠٠٠ ذراع = ١٠٠٠ سنة
     **مبالغة**. نصُّه: «the great Sabbaths Rest, of the seventh thousand years,
     may also be **shadowed by** the 7000 cubits». فهى **مشابهة** لا تحويل.
     ولو أُخذت تحويلًا لخرج ١ ذراع = ‎52.177‎ يومًا — وهو استنباطٌ لى، لا قولُه.""")


# ─────────────────────────────────────────────────────────────────────
# ٣. اختبار «التوافق»
# ─────────────────────────────────────────────────────────────────────

HEADLINE = [24, 120, 1600, 1500, 1260, 187, 3600, 480, 144, 2300, 1290, 1335, 3000, 2520]


def harmony(per_num, page_of):
    hdr("٣. اختبار «التوافق» بضابط مُطابِق")
    print("  **التصريح قبل النظر:**")
    print("   • المقياس: عدد الوحدات المختلفة التى يُقرن بها الرقم فى الكتاب.")
    print("   • الضابط: أعدادٌ أخرى فى الكتاب **فى مثل تكرارها بالصفحات**.")
    print("   • السؤال: هل تسبح أعداد الكتاب فى وحداتٍ أكثر من أقرانها؟")
    print("     ولو سبحت: هل ذلك دليلٌ على النصّ، أم على اختيار المؤلف؟\n")
    print(f"  {'العدد':>6} {'صفحات':>6} {'وحدات':>6} {'أقران':>6} {'متوسطهم':>8} {'فوقهم؟':>7}")
    above = testable = 0
    for t in sorted(HEADLINE, key=lambda x: -len(per_num.get(x, ()))):
        if t not in per_num:
            print(f"  {t:>6}  — لا يرد مقرونًا بوحدة —")
            continue
        f = len(page_of[t])
        peers = [len(per_num[m]) for m in per_num if m != t and len(page_of[m]) == f]
        if not peers:
            print(f"  {t:>6} {f:>6} {len(per_num[t]):>6} {0:>6} {'—':>8} {'—':>7}")
            continue
        mu = statistics.mean(peers)
        up = len(per_num[t]) > mu
        testable += 1
        above += up
        print(f"  {t:>6} {f:>6} {len(per_num[t]):>6} {len(peers):>6} {mu:>8.2f} "
              f"{'نعم' if up else 'لا':>7}")
    print(f"\n  الحصيلة: {above}/{testable} من أعداد الكتاب فوق أقرانها "
          f"({100*above/max(testable,1):.0f}%).")
    print("""
  ⇒ **القراءة:** النتيجة تقول إن الكتاب **يعمل بمذهبه**: الأعداد التى يهتم بها
     هى الأعداد التى يُكرّرها فى وحداتٍ متعدّدة. فهذا **اتّساقُ مؤلِّف**، لا
     دليلٌ على النصّ.

     والفرق حاسم: لو كان التوافق فى النصّ، لظهر فى أعدادٍ لم يخترها هو. أما
     فهو الذى يختار الرقم والوحدة والموضع — ثم نقيس اختياره فيبدو مُحكمًا.
     **وهذا هو عين الخطأ الذى يقع فيه من يجرّب الأرقام على السعر:** يجرّب
     حتى يُصادف، ثم يُسمّى المصادفة توافقًا.

  ⇒ ولذلك يُعامل ١٦٦٧ كـ**مصدر نحوٍ** لا كـ**دليل قياس**: يعلّمنى كيف أُقرن
     العدد بوحدته، ولا يُثبت لى أن أى اقترانٍ منها صحيح.""")


# ─────────────────────────────────────────────────────────────────────
# ٤. النحو على جان والسعر
# ─────────────────────────────────────────────────────────────────────

EGX_UNITS = [("قرش", 1, "١ جنيه = ١٠٠ قرش"), ("جنيه", 100, "الوحدة الأصلية"),
             ("نقطة", 1, "نظير point عند جان"), ("دولار", 100 * 73, "بسعر ٧٣")]


def on_price(price=38.0):
    hdr("٤. النحو على السعر — الوحدة تُغيّر الدرجة")
    print(f"  السعر كما يُكتب عادةً: «{price:.0f}» — **بلا وحدة**.\n")
    print(f"  {'الوحدة':8} {'المقدار':>12} {'الدرجة (mod 360)':>18}  ملاحظة")
    for name, mult, note in EGX_UNITS:
        q = price * mult
        print(f"  {name:8} {q:>12,.2f} {q % 360:>18.2f}°  {note}")
    print("""
  ⇒ من رقمٍ واحد تخرج أربع درجات مختلفة. والفرق ليس حسابًا خاطئًا، بل
     **تعيينًا للوحدة**. ومن لم يُعلن وحدته قبل النظر اختار الدرجة التى تُوافق
     ما يريد — وهو الفرق بين قياسٍ واختيار.

  ⇒ وفى خطاب القهوة (١٩/٣/١٩٥٤) يُعلن جان وحدته بنفسه:
     «one point to one degree» · «30 points to one degree» ·
     «12 points to one degree» · «one cent to one degree»
     فالسعر 8729 يُقرأ ‎89.00°‎ بنقطةٍ لكل درجة، و‎87.29°‎ بسنتٍ لكل درجة.
     **والوحدة هى التى تُغيّر الدرجة، لا الحساب.**""")
    print("""
  ⇒ والذى يربط الثلاثة: **٣٦٠**. دائرة جان ٣٦٠ درجة · وسنة دانيال ٣٦٠ يومًا ·
     وسنة صاحب ١٦٦٧ ٣٦٠ يومًا (ص٤٨). فالدائرة والزمن يقفان على العدد نفسه —
     **وهذا هو المبرَّر الوحيد** لقراءة السعر فى الدرجات: أن السعر والزمن
     يُقاسان بوحدةٍ واحدة هى ٣٦٠. وما عدا ذلك اختيار.""")


# ─────────────────────────────────────────────────────────────────────
# ٥. أىّ عدٍّ للأيام يصلح لهذا السوق؟
# ─────────────────────────────────────────────────────────────────────

def daycount(csv_path="/tmp/egx_clean.csv"):
    hdr("٥. عدُّ الأيام — أىّ يومٍ نعدّ؟")
    if not os.path.exists(csv_path):
        print(f"  (لا {csv_path})")
        return
    import csv as _csv
    days = set()
    with open(csv_path, newline="", encoding="utf-8", errors="ignore") as f:
        for r in _csv.DictReader(f):
            d = r["date"][:10]
            if d[:4].isdigit():
                days.add(d)
    per = collections.Counter(d[:4] for d in days)
    years = [y for y in per if per[y] > 200]
    mean = sum(per[y] for y in years) / len(years)
    print(f"  أيام التداول فى السنة (سنوات كاملة، {len(years)} سنة): "
          f"**{mean:.1f}** (أدنى {min(per[y] for y in years)} · أعلى {max(per[y] for y in years)})")
    print(f"  فأيام التقويم ÷ أيام التداول = 365.2422 ÷ {mean:.1f} = **{365.2422/mean:.2f}**")
    print(f"""
  ⇒ **النتيجة الحاسمة:** لا يوجد فى هذا الأرشيف ٣٦٠ شمعة فى السنة، بل ‎{mean:.0f}‎.
     فمن عدّ «٢٥٢٠ شمعة» ظنَّ أنه عدّ ٧ سنين، وهو عدّ **‎{2520/mean:.1f}‎** سنة
     تقويمية. ومن عدّ ٢٥٢٠ **يومًا تقويميًّا** فقد عدّ ٧ سنين نبوية
     (= ‎{2520/365.2422:.2f}‎ سنة شمسية). والفرق بين العدّين **‎{2520/mean - 2520/365.2422:.1f}‎**
     سنة — وهو فرقٌ يُسقط أى اختبارٍ لا يُصرّح بعدِّه.

  ⇒ ولذلك: **التقويم ٣٦٠ يُعدّ أيامًا لا شموعًا.** والذى استُخدم فى
     `tools/biblical_time.py §٥` كان أيامًا تقويمية (‎(d − anchor).days‎) —
     فهو على التقويم الصحيح. أما لو عُدَّت الشموع لكان الاختبار كلُّه عن
     دورةٍ أخرى لا عن دورة دانيال.

  ⇒ وهذا يفسّر أيضًا خطأً شائعًا فى قراءة «نقطة = يوم»: المقياس يُكتب فى
     **تقويم**، والسوق يعمل فى **تقويمٍ آخر**. وأى تحويل بينهما يمرّ بـ
     ‎{365.2422/mean:.2f}‎.""")


def main():
    pages = load()
    locks(pages)
    per_num, page_of = inventory(pages)
    calendar()
    harmony(per_num, page_of)
    daycount()
    on_price()
    print("\n" + LINE)
    print(" الخلاصة: ١٦٦٧ يُعطى النحو والتقويم (٣٦٠/٣٠/٢٤) ويُعطى اتّساقه؛")
    print("          ولا يُعطى دليلًا. والدليل يُشترى بالتصريح المسبق وبالضابط.")
    print(LINE)


if __name__ == "__main__":
    main()
