#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحويل السعر إلى طول فلكي كما في كتاب ميكولا — وفي الخريطتين معًا.

الكتابان: Gann's Scientific Methods Unveiled — الجزء الأول (1995/1996) والثاني.
    الجزء 1، الفصل 8: Price & Longitude Conversion
    الجزء 2، الفصل 2: Price & Longitude Conversion Part 2
    الجزء 1، الفصل 10: The Hexagon Chart and Square of Nine

وفي الكتاب **خريطتان مختلفتان** لتحويل السعر إلى درجة، ولا تتفقان:

    1) تحويل السعر والطول (الفصل 8):  السعر **هو** الدرجة.
       السعر 97.5 = 97.5° تراكمية = 7° 30' في السرطان.
       وإضافة 360 تعطي نفس الدرجة في برج آخر: 97.5 · 457.5 · 817.5 ...

    2) مربع التسعة (الفصل 10):  السعر يأخذ درجته من **موضعه على اللولب**.
       الدرجة = (√N × 180 − 225) mod 360
       فالسعر 144 يقع على 135° — لا على 144°.

والفرق بين الخريطتين يصل إلى 149 درجة. أي أن السعر الواحد له **موضعان**
حسب الأداة المستعملة. وهذا ليس خطأ في الحساب، بل خاصية في المنهج نفسه.

التشغيل:
    python3 tools/mikula_price_longitude.py 97.5
    python3 tools/mikula_price_longitude.py --compare 38 144 334
    python3 tools/mikula_price_longitude.py --aspect 97.5 277.5
"""

import math
import sys

SIGNS = [
    "الحمل", "الثور", "الجوزاء", "السرطان", "الأسد", "العذراء",
    "الميزان", "العقرب", "القوس", "الجدي", "الدلو", "الحوت",
]

# الأوجه التي يستعملها ميكولا في الفصل 8 والفصل 10
ASPECTS = [
    (0.0, "اقتران (0°)"),
    (60.0, "تسديس (60°)"),
    (90.0, "تربيع (90°)"),
    (120.0, "تثليث (120°)"),
    (180.0, "تقابل (180°)"),
]


def price_to_longitude(price: float) -> float:
    """تحويل ميكولا: السعر هو الدرجة. يعيد الطول التراكمي 0..360."""
    return price % 360.0


def describe(longitude: float) -> str:
    lon = longitude % 360.0
    sign = SIGNS[int(lon // 30) % 12]
    deg = int(lon % 30)
    minutes = round((lon % 30 - deg) * 60)
    if minutes == 60:
        deg, minutes = deg + 1, 0
    return f"{deg}° {minutes:02d}' {sign}"


def equivalent_prices(price: float, count: int = 5) -> list:
    """الأسعار التي تعطي الدرجة نفسها بإضافة 360."""
    return [price + 360.0 * k for k in range(count)]


def minutes_to_fraction(minutes: float) -> float:
    """دقائق القوس إلى كسر في السعر — كما في جدول 8-3: 26' = 0.43."""
    return minutes / 60.0


def so9_cell(n: int) -> float:
    """مربع التسعة: درجة **خلية** صحيحة. المربع لا يحمل كسورًا."""
    if float(n) != int(n):
        raise ValueError(f"{n} ليس خلية — المربع التسعة لا يحمل كسورًا")
    if n <= 0:
        raise ValueError("الخلية يجب أن تكون موجبة")
    return (math.sqrt(n) * 180.0 - 225.0) % 360.0


def so9_step(n: int) -> float:
    """العرض الزاوي للخلية n. متغيّر: أوسع عند زوايا المربع، أضيق في وسط الأضلاع."""
    return (so9_cell(n + 1) - so9_cell(n)) % 360.0


def so9_angle(n: float) -> float:
    """درجة رقم على المربع — والكسر **بين خليتين**، لا داخل الرقم.

    هذا هو نصّ ميكولا: لا تُقرَّب الخلية، بل يُقاس الكسر من موضعه
    بين الخليتين. فالـ144.5 = 144 + نصف عرض الخلية 144→145.
    """
    base = int(math.floor(n))
    frac = n - base
    if base < 1:
        raise ValueError("الرقم يجب أن يكون ≥ 1")
    return (so9_cell(base) + frac * so9_step(base)) % 360.0


def so9_subdivisions(n: int, denom: int = 8) -> list:
    """تقسيم الخلية n: الثُمن، الربع، ثلاثة أثمان… حتى الخلية التالية."""
    a0, step = so9_cell(n), so9_step(n)
    return [(k, a0 + step * k / denom) for k in range(denom + 1)]


#  ─────────────────────────────────────────────────────────────────────
#  الخريطة الدائرية (الجزء 2، الفصل 4) — القاعدة منصوصة، والقياس يثبتها
#
#  «الأرقام على الجزء الداخلي تبدأ بـ1 على يمين الحلقة الداخلية، وتتحرك
#   عكس عقارب الساعة إلى 24، ثم تخرج إلى الحلقة الثانية عند 25.
#   وفى كل حلقة أربعة وعشرون رقمًا… والخريطة الأصلية تصل إلى 576 وهو
#   مربع 24، أي أربع وعشرون حلقة.»
#
#  و«على الخريطة الدائرية 290 تقع على 0° 00' و291 على 15° 00'،
#   فنصف المسافة بينهما نصف المسافة بين هذين الطولين، أي 290‑½ = 7° 30'.»
#
#  و«السعر 554‑½ يساوي 7° 30' أو 247.5°»، و«المشتري على 10° 24'
#   أي 250.4°».
#
#  من الأخيرين: البُعد الفلكي = موضع الخريطة + 240° بالضبط.
#  تحقّق: 554.5 → 7.5 على الخريطة → 247.5 فلكيًا. ✔
#        20 أكتوبر… لا. المشتري 10°24' = 250.4° → 250.4 − 240 = 10.4 = 10°24'. ✔
#
#  والتسمية للاثنين واحدة في الكتب: «درجة». وهذا خطأ قياس:
#  موضع الخريطة ≠ الطول الفلكي، والفرق بينهما 240° ثابتة.
#  ─────────────────────────────────────────────────────────────────────

CHART_ANCHOR = 290.0   # الرقم الواقع على خط 0° من الخريطة
CHART_ZODIAC_OFFSET = 240.0  # 0° من الخريطة = 0° القوس


def circle_position(n: float) -> float:
    """موضع الرقم **على الخريطة** (0° عند 290)، لا في البروج. يقبل الكسور."""
    return (15.0 * (n - CHART_ANCHOR)) % 360.0


def circle_cell(n: int) -> float:
    """موضع **خلية** صحيحة على الخريطة. الخريطة شبكة أيضًا: 24 في الحلقة."""
    if float(n) != int(n):
        raise ValueError(f"{n} ليس خلية — استعمل circle_position() للكسور")
    return circle_position(float(n))


def circle_longitude(n: float) -> float:
    """الطول الفلكي المقابل — موضع الخريطة + 240°."""
    return (circle_position(n) + CHART_ZODIAC_OFFSET) % 360.0


def circle_angle(n: float) -> float:
    """مرادف تاريخي: الطول الفلكي على الخريطة الدائرية."""
    return circle_longitude(n)


def angular_separation(a: float, b: float) -> float:
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def nearest_aspect(a: float, b: float, orb: float = 3.0):
    """أقرب وجه بين طولين، ومسافة الخطأ."""
    sep = angular_separation(a, b)
    best = min(ASPECTS, key=lambda x: abs(sep - x[0]))
    diff = abs(sep - best[0])
    return best[1], sep, diff, diff <= orb


def compare_table(prices) -> None:
    print(f"{'السعر':>9} {'تحويل 1:1':>13} {'الموضع':>20} "
          f"{'مربع التسعة':>13} {'الموضع':>20} {'الفرق':>8}")
    for p in prices:
        a, b = price_to_longitude(p), so9_angle(p)
        diff = (a - b + 180.0) % 360.0 - 180.0
        print(f"{p:>9} {a:>12.2f}° {describe(a):>20} "
              f"{b:>12.2f}° {describe(b):>20} {diff:>+7.1f}°")


#  ─────────────────────────────────────────────────────────────────────
#  البحث عن أسعار تقارب درجة — ومعه ضابط العشوائية
#
#  المطابقة وحدها ليست اكتشافًا: لو كان السعر موزّعًا بانتظام على الدائرة
#  لوقع 2×الأورب/360 من الأسعار فى أى درجة. فإن كانت الأسعار متكدّسة عند
#  الأرقام الصغيرة، فبعض الدرجات تعطى عشرات المطابقات وأخرى صفرًا — بلا
#  أن يكون فى السوق شىء. فالضابط إلزامى: توزيع المطابقات على الـ360 درجة
#  كلها، ثم موقع درجتنا منه.
#  ─────────────────────────────────────────────────────────────────────


def load_prices(path):
    """يقرأ ملف CSV بصيغة: الاسم,السعر — ويتجاهل سطر العنوان."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            parts = line.replace("\t", ",").split(",")
            if len(parts) < 2:
                continue
            try:
                price = float(parts[-1].replace(",", "").strip())
            except ValueError:
                continue
            out.append((",".join(parts[:-1]).strip() or f"#{i + 1}", price))
    return out


def _sep(price, target):
    d = abs((price % 360.0) - target) % 360.0
    return min(d, 360.0 - d)


def near_report(target, prices, orb=3.0):
    print(f"الدرجة المستهدفة: {target:.4f}°  ({describe(target)})")
    print(f"الأورب: ±{orb}°   |   عدد الأسعار: {len(prices)}")
    print("الوحدة: 1 جنيه = 1 درجة (خريطة 1:1)\n")

    hits = sorted((_sep(p, target), p, n) for n, p in prices if _sep(p, target) <= orb)
    print(f"المطابقات: {len(hits)}")
    for d, p, n in hits:
        print(f"   فرق {d:5.2f}° ({d * 60:5.1f}')   سعر {p:>10.2f}   طول {p % 360:7.2f}°   {n[:44]}")

    nearest = sorted((_sep(p, target), p, n) for n, p in prices)[:5]
    print("\nأقرب خمسة — مهما كان الأورب:")
    for d, p, n in nearest:
        print(f"   فرق {d:5.2f}° ({d * 60:5.1f}')   سعر {p:>10.2f}   {n[:44]}")

    counts = [sum(1 for _, p in prices if _sep(p, float(d)) <= orb) for d in range(360)]
    srt = sorted(counts)
    better = sum(1 for c in counts if c > len(hits))
    print("\nالضابط — المطابقات عند كل درجة من 360:")
    print(f"   المتوسط {sum(counts) / 360:.2f}   الوسيط {srt[180]}   الأدنى {min(counts)}   الأقصى {max(counts)}")
    print(f"   عند درجتنا: {counts[int(target) % 360]}   |   درجات تعطى أكثر منها: {better}/360 ({better / 3.6:.1f}%)")
    print(f"   أكثر درجة ازدحامًا: {counts.index(max(counts))}° بـ{max(counts)}")
    return hits


#  ─────────────────────────────────────────────────────────────────────
#  الدائرة المضاعفة — الرقم لا يتغير بنقل العلامة العشرية
#
#  123 = 12.3 = 1.23 = 0.123 = 0.0123.  فالرقم ليس موضعًا على خط،
#  بل **مانتيسا**: ما يبقى بعد إسقاط قوى العشرة.
#
#  ولا توجد دالة خطية تحقق f(10x)=f(x)، لأن الفرق 10x−x = 9x يتغير
#  مع x. فالبنية الوحيدة التى تصمد هى **ضربية**: معامل التكرار.
#
#  والخريطة: 360° لكل عقد (أى لكل معامل 10)، فالدرجة
#      d(x) = (log10 x mod 1) × 360
#  والسعر المقابل لدرجة d هو 10^(d/360) × 10^k.
#
#  وفى هذا المقياس تصبح الخريطة 1:1 ومربع التسعة والخريطة الدائرية
#  **كلها خاطئة** — كل واحدة تعطى لأرقام السلسلة الواحدة درجاتٍ متفرقة
#  تصل إلى 333°. والقياس فى §22.2.
#  ─────────────────────────────────────────────────────────────────────


def multiplicative_degree(value: float) -> float:
    """درجة الرقم على الدائرة المضاعفة — لا تتغير بنقل العلامة."""
    if value == 0:
        raise ValueError("الصفر لا موضع له على دائرة مضاعفة")
    return (math.log10(abs(value)) % 1.0) * 360.0


def multiplicative_family(degree: float, count: int = 6) -> list:
    """كل الأسعار التى تقع على درجة واحدة — وهى رقم واحد بعلامات مختلفة."""
    d = degree % 360.0
    base = 10 ** (d / 360.0)
    k0 = -2
    return [round(base * 10 ** (k0 + i), 6) for i in range(count)]


def near_report_log(target, prices, orb=3.0):
    def deg(p):
        return multiplicative_degree(p)

    hits = sorted((angular_separation(deg(p), target), p, n) for n, p in prices
                  if angular_separation(deg(p), target) <= orb)
    print(f"الدرجة المستهدفة: {target:.4f}°  ({describe(target)})")
    print(f"الأورب: ±{orb}°  =  ±{100 * (10 ** (orb / 360.0) - 1):.2f}% سعرًا")
    print(f"الأسعار المكافئة: {', '.join(f'{x:g}' for x in multiplicative_family(target))}")
    print(f"عدد الأسعار: {len(prices)}\n")
    print(f"المطابقات: {len(hits)}")
    for d, p, n in hits:
        k = math.floor(math.log10(p))
        print(f"   فرق {d:5.2f}°   سعر {p:>10.3f}  (= {p / 10 ** k:.4f}×10^{k})   {n[:44]}")
    print("\nأقرب خمسة:")
    for d, p, n in sorted((angular_separation(deg(p), target), p, n) for n, p in prices)[:5]:
        print(f"   فرق {d:5.2f}°   سعر {p:>10.3f}   {n[:44]}")
    counts = [sum(1 for _, p in prices if angular_separation(deg(p), float(d)) <= orb) for d in range(360)]
    srt = sorted(counts)
    print("\nالضابط — المطابقات عند كل درجة من 360:")
    print(f"   المتوسط {sum(counts) / 360:.2f}   الوسيط {srt[180]}   الأدنى {min(counts)}   الأقصى {max(counts)}")
    print(f"   عند درجتنا: {counts[int(target) % 360]}   |   درجات تعطى أكثر: "
          f"{sum(1 for c in counts if c > len(hits))}/360")
    print(f"   أكثر درجة ازدحامًا: {counts.index(max(counts))}° بـ{max(counts)}")
    return hits


#  ─────────────────────────────────────────────────────────────────────
#  الصورة الفردية والزوجية — ودائرة العقدين
#
#  √12 = √1200 = √120000  (3.4641 · 34.641 · 346.41)
#  √5  = √500  = √50000   (2.2361 · 22.3607 · 223.607)
#
#  لأن √(x·100) = √x × 10. فالأسرة تتقدّم بمعامل 100 لا 10.
#  والسبب: الأس (الجزء الصحيح من اللوغاريتم) يحدد **الصورة**:
#      الأس زوجى → صورة زوجية   |   الأس فردى → صورة فردية
#  و÷100 يحذف رقمين فيحفظ الصورة، و÷10 يحذف رقمًا فيقلبها.
#  وهذا نصّ ما قاله المستخدم عن تقسيم جان على 10 أو 100.
#
#  وعلى دائرة العقد الواحد (360° لكل ×10) تسقط الصورة: 12 و120 و1200
#  كلها 28.505° — فلا يمكن أخذ جذر لا يعرف أيّهما. فالصورة تحتاج
#  **دائرتين**: 720° لكل ×100، أى 360° لكل عقدين.
#  وعليها: 12 و1200 = 194.253°، و120 = 14.253° — متقابلان بـ180° بالضبط.
#  ─────────────────────────────────────────────────────────────────────


def number_form(value: float) -> str:
    """الصورة الفردية أو الزوجية — بتكافؤ الأس. وتحفظها القسمة على 100."""
    if value <= 0:
        raise ValueError("الرقم يجب أن يكون موجبًا")
    return "فردية" if math.floor(math.log10(value)) % 2 else "زوجية"


def two_decade_degree(value: float) -> float:
    """الدرجة على دائرة العقدين — الصورة الفردية والزوجية نقطتان متقابلتان."""
    if value <= 0:
        raise ValueError("الرقم يجب أن يكون موجبًا")
    return (math.log10(value) % 2.0) / 2.0 * 360.0


def two_decade_family(degree: float, count: int = 6) -> list:
    """أرقام الدرجة على دائرة العقدين — أسرة واحدة تفصلها ×100."""
    base = 10 ** (2.0 * (degree % 360.0) / 360.0)
    k0 = -3 if base < 1 else -1
    return [round(base * 100 ** k, 6) for k in range(k0, k0 + count)]


def near_report_two(target, prices, orb=3.0):
    def deg(p):
        return two_decade_degree(p)

    hits = sorted((angular_separation(deg(p), target), p, n) for n, p in prices
                  if angular_separation(deg(p), target) <= orb)
    print(f"دائرة العقدين — الهدف {target:.4f}°  ({describe(target)})")
    print(f"الأورب ±{orb}°  =  ±{100 * (10 ** (2 * orb / 360.0) - 1):.2f}% سعرًا")
    print(f"الأسرة: {', '.join(f'{x:g}' for x in two_decade_family(target))}\n")
    print(f"المطابقات: {len(hits)}")
    for d, p, n in hits:
        print(f"   فرق {d:5.3f}°   سعر {p:>10.3f}   {number_form(p):<6}   {n[:42]}")
    mins = [min(angular_separation(deg(p), float(d)) for _, p in prices) for d in range(360)]
    here = min(angular_separation(deg(p), target) for _, p in prices)
    print(f"\nأقرب سهم: {here:.4f}° — ومرتبته بين 360 درجة: "
          f"{sum(1 for x in mins if x < here) + 1}  (وسيط الأقرب {sorted(mins)[180]:.3f}°)")
    counts = [sum(1 for _, p in prices if angular_separation(deg(p), float(d)) <= orb) for d in range(360)]
    print(f"مطابقات عند درجتنا: {len(hits)}  |  المتوسط {sum(counts) / 360:.2f}  "
          f"|  درجات أكثر: {sum(1 for c in counts if c > len(hits))}/360")
    return hits


#  ─────────────────────────────────────────────────────────────────────
#  سلاسل الأرقام: فردية متجاورة (1357) · زوجية متجاورة (2468) · متشكلة (1234)
#
#  الخطوة بين الأرقام هى **نصف قطر الحلقة**:
#      +2 فى الجذر = دورة كاملة على المربع  → (√N + 2)²
#      +1 فى الجذر = نصف دورة               → الركن المقابل
#
#  فـ1 3 5 7 كلها على 315°، و2 4 6 8 كلها على 135° — يفصلها 180°.
#  و1 2 3 4 تتبادل بين الركنين، ولهذا هى «متشكلة».
#
#  والطاقة: كل سلسلة تولّد عائلة مجسّمة.
#      1 3 5 7 → مجاميعها 1 4 9 16  (مربعات) — لأن n²−(n−1)² = 2n−1
#      2 4 6 8 → مجاميعها 2 6 12 20 (مستطيلة)
#      1 2 3 4 → مجاميعها 1 3 6 10  (مثلثة)
#  أى أن السلسلة الفردية هى **قاعدة بناء المربع نفسه** — لا مثالًا عليه.
#  ─────────────────────────────────────────────────────────────────────


def pattern_report(text):
    digits = [int(c) for c in str(text) if c.isdigit()]
    steps = sorted({b - a for a, b in zip(digits, digits[1:])})
    print(f"السلسلة: {' '.join(map(str, digits))}   (الخطوة: {steps})")
    print(f"{'الرقم':>6}{'مربعه':>10}{'على المربع':>13}{'الحلقة':>9}")
    for d in digits:
        r = (d - 1) // 2
        print(f"{d:>6}{d * d:>10}{so9_cell(d * d):>12.3f}°{r:>9}")
    acc, tot = [], 0
    for d in digits:
        tot += d
        acc.append(tot)
    fam = "مربعات كاملة" if steps == [2] and digits[0] % 2 else (
        "مستطيلة" if steps == [2] else "مثلثة" if steps == [1] else "—")
    print(f"\nالمجاميع التراكمية: {acc}   →   {fam}")
    val = float("".join(str(d) for d in digits))
    print(f"والعدد {val:g} نفسه: جذره {math.sqrt(val):.4f} → درجة {so9_angle(val):.3f}°")
    print("   (السلاسل تصف موضع **الجذور**، لا موضع العدد — انظر §24.6)")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("استعمل: <سعر>  |  --compare p1 p2 ...  |  --aspect سعر طول  |  --fractions [n]  |  --near درجة --prices ملف")
        return

    if args[0] == "--compare":
        compare_table([float(x) for x in args[1:]] or [38, 97.5, 144, 334])
        return

    if args[0] == "--near":
        import argparse
        ap = argparse.ArgumentParser()
        ap.add_argument("--near", type=float, required=True)
        ap.add_argument("--orb", type=float, default=3.0)
        ap.add_argument("--prices", required=True)
        ap.add_argument("--log", action="store_true")
        ap.add_argument("--log2", action="store_true")
        ns = ap.parse_args(args)
        if ns.log2:
            near_report_two(ns.near, load_prices(ns.prices), ns.orb)
            return
        if ns.log:
            near_report_log(ns.near, load_prices(ns.prices), ns.orb)
        else:
            near_report(ns.near, load_prices(ns.prices), ns.orb)
        return

    if args[0] == "--pattern":
        for tok in args[1:] or ["1357", "2468", "1234"]:
            pattern_report(tok)
            print()
        return

    if args[0] == "--form":
        for tok in args[1:]:
            v = float(tok)
            print(f"   {v:>10g}   {number_form(v):<6}   عقد واحد {multiplicative_degree(v):8.3f}°   "
                  f"عقدان {two_decade_degree(v):8.3f}°")
        return

    if args[0] == "--mul":
        deg = float(args[1]) if len(args) > 1 else 207.092
        print(f"الدرجة {deg:.3f}° = {describe(deg)}")
        print("عائلة الأسعار المكافئة (رقم واحد بعلامات مختلفة):")
        for v in multiplicative_family(deg, 7):
            print(f"   {v:>14g}   → {multiplicative_degree(v):9.4f}°")
        print(f"\nو123 على الدائرة المضاعفة: {multiplicative_degree(123):.4f}°")
        print(f"و12.3: {multiplicative_degree(12.3):.4f}°   و0.0123: {multiplicative_degree(0.0123):.4f}°")
        return

    if args[0] == "--fractions":
        n = int(args[1]) if len(args) > 1 else 144
        print(f"تقسيم الخلية {n} → {n + 1}")
        print(f"عرض الخلية كاملًا = {so9_step(n):.4f}°")
        print(f"{'الموضع':<16}{'على المربع':>13}{'على الدائرة':>14}")
        for k, ang in so9_subdivisions(n, 8):
            label = f"{n}" if k == 0 else (f"{n} + {k}/8" if k < 8 else f"{n + 1}")
            print(f"{label:<16}{ang:>12.4f}°{circle_longitude(n + k / 8.0):>13.4f}°")
        print()
        print(f"ومثال ميكولا الحرفي: 290 ← موضع {circle_cell(290):.1f}° / فلكي "
              f"{circle_angle(290):.1f}° ، 291 ← فلكي {circle_angle(291):.1f}° ، "
              f"290.5 ← فلكي {circle_angle(290.5):.1f}°")
        print(f"وعلى الخريطة: 554.5 ← موضع {circle_position(554.5):.1f}° ، "
              f"فلكي {circle_angle(554.5):.1f}°  (والكتاب: 247.5°)")
        return

    if args[0] == "--aspect":
        price, lon = float(args[1]), float(args[2])
        name, sep, err, ok = nearest_aspect(price_to_longitude(price), lon)
        print(f"السعر {price} ← {price_to_longitude(price):.2f}° = "
              f"{describe(price_to_longitude(price))}")
        print(f"طول الكوكب {lon:.2f}° = {describe(lon)}")
        print(f"الفصل {sep:.2f}° → أقرب وجه: {name} (خطأ {err:.2f}°) "
              f"{'داخل السماحية' if ok else 'خارج السماحية'}")
        return

    p = float(args[0])
    lon = price_to_longitude(p)
    print(f"السعر {p:g}  ←  {lon:.4f}°  =  {describe(lon)}")
    print(f"الأسعار المكافئة (+360): {', '.join(f'{x:g}' for x in equivalent_prices(p))}")
    print(f"موضعه على مربع التسعة: {so9_angle(p):.2f}°  =  {describe(so9_angle(p))}")
    if p == int(p):
        print(f"  عرض خليته ({int(p)} → {int(p)+1}) = {so9_step(int(p)):.4f}°")


if __name__ == "__main__":
    main()
