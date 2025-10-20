import io
import matplotlib.pyplot as plt
from aiogram.types import BufferedInputFile
import calendar

async def generate_year_chart(year: int, data):
    months = [int(row[0]) for row in data]
    totals = [float(row[1]) for row in data]

    plt.figure(figsize=(7, 4))
    plt.bar(months, totals, color="skyblue")
    plt.title(f"{year}-yil bo‘yicha oylik harajatlar")
    plt.xlabel("Oy")
    plt.ylabel("So‘m")
    plt.xticks(months)
    plt.grid(True, linestyle="--", alpha=0.6)

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return BufferedInputFile(buf.read(), filename=f"{year}_year_chart.png")


async def generate_month_chart(year: int, month: int, data):
    day_totals = {int(row[0]): float(row[1]) for row in data}
    num_days = calendar.monthrange(year, month)[1]
    days = list(range(1, num_days + 1))

    totals = [day_totals.get(day, 0) for day in days]

    plt.figure(figsize=(8, 4))
    plt.plot(days, totals, marker="o", linewidth=2, color="royalblue")
    plt.title(f"{calendar.month_name[month]} {year} oyi harajatlari")
    plt.xlabel("Kun")
    plt.ylabel("Harajat (so‘m)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    return BufferedInputFile(buf.read(), filename=f"{year}_{month}_month_chart.png")