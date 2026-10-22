#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حساب تواريخ اقتران المشتري بزحل في **الإطارين**: المركزي الأرضي والمركزي الشمسي.

الغرض: «دورة العشرين سنة» رقم يُتنازع عليه (19.53 · 19.86 · 20)، وكل نزاع
يُحسم بالتواريخ لا بالحجة. لكن هناك سؤال أسبق: **أي إطار؟**

- **مركزي أرضي (geocentric):** ما يُرى من الأرض — وهو إطار التنجيم
  وإطار جداول جان وجنكينز. يُقاس بالطول السماوي الظاهر للكوكبين.
- **مركزي شمسي (heliocentric):** ما يقع حول الشمس — وهو إطار الميكانيكا.
  يُقاس بالطول الشمسي للكوكبين حول الشمس.

المتوسط واحد تقريبًا في الإطارين (لأنه فرق السرعتين الزاويتين)، لكن
**التواريخ تختلف**، ومقدار الاختلاف هو ما يقيسه هذا الملف.

الطريقة: عناصر مدارية كبلرية وسطية (JPL، صالحة 1800–2050)، حل معادلة
كبلر، ثم الاقتران عند تساوي الطول في الإطار المطلوب.

التشغيل:
    python3 tools/astro_conjunctions.py 1900 2050            # الإطاران
    python3 tools/astro_conjunctions.py 1900 2050 --frame geo
    python3 tools/astro_conjunctions.py 1900 2050 --frame helio
"""

import math
import sys

D2R = math.pi / 180.0
R2D = 180.0 / math.pi

# عناصر مدارية وسطية عند J2000.0 ومعدلاتها لكل قرن يولياني
# a (AU), e, I (deg), L (deg), long.peri (deg), long.node (deg)
ELEMENTS = {
    # عطارد والزهرة والمريخ — تُضاف للاختبار الفلكى (الزوايا)، ولها نفس المرجع J2000.
    "mercury": (
        (0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593),
        (0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081),
    ),
    "venus": (
        (0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255),
        (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418),
    ),
    "mars": (
        (1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891),
        (0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343),
    ),
    "earth": (
        (1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0),
        (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0),
    ),
    "jupiter": (
        (5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909),
        (-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106),
    ),
    "saturn": (
        (9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448),
        (-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794),
    ),
    # أورانوس ونبتون: خارج BODIES (الذى يبقى ستة أجرام)، ويُستعملان عند الحاجة فقط.
    # ضبط أورانوس: دخول الجوزاء 2025-07-07 معطًى 59.64° أى 0.36° قبل العتبة.
    "uranus": (
        (19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503),
        (-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589),
    ),
    "neptune": (
        (30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574),
        (0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664),
    ),
    # بلوتو: دقته أضعف (مداره شاذ)، ويُستعمل فقط فى خطابى جان (§23).
    "pluto": (
        (39.48211675, 0.24882730, 17.14001206, 238.92903833, 224.06891629, 110.30393684),
        (-0.00031596, 0.00005170, 0.00004818, 145.20780515, -0.04062942, -0.01183482),
    ),
}


def heliocentric(name, jd):
    """إحداثيات مركزية شمسية بالنظام السماوي (AU)."""
    base, rate = ELEMENTS[name]
    T = (jd - 2451545.0) / 36525.0
    a, e, inc, L, peri, node = [b + r * T for b, r in zip(base, rate)]

    M = (L - peri) % 360.0
    E = M * D2R
    for _ in range(60):
        dE = (E - e * math.sin(E) - M * D2R) / (1.0 - e * math.cos(E))
        E -= dE
        if abs(dE) < 1e-12:
            break

    xp = a * (math.cos(E) - e)
    yp = a * math.sqrt(1.0 - e * e) * math.sin(E)

    w = (peri - node) * D2R
    om = node * D2R
    i = inc * D2R

    cw, sw = math.cos(w), math.sin(w)
    co, so = math.cos(om), math.sin(om)
    ci, si = math.cos(i), math.sin(i)

    x = (cw * co - sw * so * ci) * xp + (-sw * co - cw * so * ci) * yp
    y = (cw * so + sw * co * ci) * xp + (-sw * so + cw * co * ci) * yp
    z = (sw * si) * xp + (cw * si) * yp
    return x, y, z


def longitude(name, jd, frame):
    """الطول السماوي (راديان) في الإطار المطلوب."""
    px, py, _ = heliocentric(name, jd)
    if frame == "helio":
        return math.atan2(py, px) % (2 * math.pi)
    ex, ey, _ = heliocentric("earth", jd)
    return math.atan2(py - ey, px - ex) % (2 * math.pi)


def sun_longitude(jd):
    """الطول الظاهرى للشمس (مركزي أرضى، اعتدال التاريخ) — قياس لا اصطلاح.

    الطول الفلكى يحتسب الاعتدال الربيعى الحقيقى صفرًا. وعناصر كبلر المرجعية
    عند J2000، فيُضاف التقدّم المحورى (precession) لتحويلها إلى اعتدال
    التاريخ. وبعد التصحيح يطابق الاعتدال الربيعى 2026 المنشور (14:46 UT)
    بخطأ 12 دقيقة = 0.008°.
    """
    e = longitude("earth", jd, "helio") * R2D
    T = (jd - 2451545.0) / 36525.0
    prec = (5029.0966 * T + 1.11113 * T * T) / 3600.0
    return ((e + 180.0) % 360.0 + prec) % 360.0


BODIES = ("sun", "mercury", "venus", "mars", "jupiter", "saturn")


def body_longitude(name, jd):
    """الطول السماوى الظاهرى (درجات) لكل الأجرام فى إطار واحد (اعتدال J2000).

    الشمس تُشتق من الأرض المركزية الشمسية + 180، بلا تصحيح التقدّم المحورى —
    لأن الاختلاف بين كوكبين هو المقصود، وأى إزاحة ثابتة تسقط فى الطرح.
    """
    if name == "sun":
        return (longitude("earth", jd, "helio") * R2D + 180.0) % 360.0
    return longitude(name, jd, "geo") * R2D


SIGNS = ("الحمل", "الثور", "الجوزاء", "السرطان", "الأسد", "العذراء",
         "الميزان", "العقرب", "القوس", "الجدي", "الدلو", "الحوت")


def sign_notation(deg):
    """درجة ← «27° 05' الميزان»."""
    d = int(deg % 30)
    m = (deg % 30 - d) * 60
    return f"{d}° {int(m):02d}' {SIGNS[int(deg // 30)]}"


def date_to_jd(y, m, d, hours=0.0):
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5 + hours / 24.0


def diff(jd, frame):
    d = (longitude("jupiter", jd, frame) - longitude("saturn", jd, frame)) % (2 * math.pi)
    if d > math.pi:
        d -= 2 * math.pi
    return d * R2D


def jd_to_date(jd):
    jd += 0.5
    Z = int(jd)
    F = jd - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - alpha // 4
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)
    day = B - D - int(30.6001 * E) + F
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715
    return year, month, int(day)


def find_conjunctions(jd_start, jd_end, frame, step=2.0):
    """كل مقابلة للكوكبين، ثم تُجمع المتقاربة في «موسم اقتران» واحد.

    الاقتران المركزي الأرضي قد يتكرر ثلاث مرات في أشهر قليلة بسبب التراجع،
    فتُعدّ المقابلات التي بينها أقل من 400 يوم موسمًا واحدًا.
    الاقتران الشمسي واحد لا يتكرر، لكن نفس التجميع آمن.
    """
    crossings = []
    t = jd_start
    prev = diff(t, frame)
    while t < jd_end:
        t_next = t + step
        cur = diff(t_next, frame)
        if (prev < 0.0 <= cur or prev > 0.0 >= cur) and abs(cur - prev) < 180.0:
            lo, hi = t, t_next
            lo_diff = prev
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                if (diff(mid, frame) < 0.0) == (lo_diff < 0.0):
                    lo = mid
                else:
                    hi = mid
            crossings.append(0.5 * (lo + hi))
        prev = cur
        t = t_next

    seasons = []
    for jd in crossings:
        if seasons and (jd - seasons[-1][-1]) < 400.0:
            seasons[-1].append(jd)
        else:
            seasons.append([jd])
    return [sum(s) / len(s) for s in seasons]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    frame_arg = "both"
    for i, a in enumerate(sys.argv):
        if a == "--frame" and i + 1 < len(sys.argv):
            frame_arg = sys.argv[i + 1]
    y0 = int(args[0]) if args else 1900
    y1 = int(args[1]) if len(args) > 1 else 2050

    jd0 = 2415020.5 + (y0 - 1900) * 365.25
    jd1 = 2415020.5 + (y1 - 1900) * 365.25

    frames = ["geo", "helio"] if frame_arg == "both" else [frame_arg]
    results = {}
    for fr in frames:
        results[fr] = find_conjunctions(jd0, jd1, fr)

    label = {"geo": "مركزي أرضي (ما يُرى من الأرض)", "helio": "مركزي شمسي (حول الشمس)"}

    for fr in frames:
        cj = results[fr]
        print()
        print("=" * 68)
        print(f"  {label[fr]}  —  {fr}")
        print("=" * 68)
        print(f"{'#':>3}  {'التاريخ':<12} {'الفاصل (سنة)':>12}")
        prev = None
        for k, jd in enumerate(cj, 1):
            y, m, d = jd_to_date(jd)
            gap = (jd - prev) / 365.2422 if prev else float("nan")
            gap_s = f"{gap:12.3f}" if prev else f"{'—':>12}"
            print(f"{k:>3}  {y:04d}-{m:02d}-{d:02d}   {gap_s}")
            prev = jd
        if len(cj) > 1:
            gaps = [(b - a) / 365.2422 for a, b in zip(cj, cj[1:])]
            print()
            print(f"  المتوسط {sum(gaps)/len(gaps):.4f} · الأصغر {min(gaps):.3f} · "
                  f"الأكبر {max(gaps):.3f} · المدى {max(gaps)-min(gaps):.3f}")

    if len(frames) == 2:
        g, h = results["geo"], results["helio"]
        print()
        print("=" * 68)
        print("  الفرق بين الإطارين لكل اقتران")
        print("=" * 68)
        print(f"{'#':>3}  {'شمسي':<12} {'أرضي':<12} {'الفرق (يوم)':>13}")
        for i, hd in enumerate(h):
            # أقرب اقتران أرضي
            near = min(g, key=lambda x: abs(x - hd)) if g else None
            if near is None:
                continue
            hy, hm, hdd = jd_to_date(hd)
            gy, gm, gdd = jd_to_date(near)
            print(f"{i+1:>3}  {hy:04d}-{hm:02d}-{hdd:02d}   "
                  f"{gy:04d}-{gm:02d}-{gdd:02d}   {near - hd:+13.1f}")


if __name__ == "__main__":
    main()
