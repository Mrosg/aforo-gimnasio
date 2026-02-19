import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

CSV_FILE = "aforo_dreamfit.csv"

# --- Cargar datos ---
df = pd.read_csv(CSV_FILE)
df["hora"] = pd.to_datetime(df["hora"])
df["personas"] = pd.to_numeric(df["personas"])
df["porcentaje_num"] = df["porcentaje"].str.replace("%", "").astype(int)

# --- Calcular la semana actual (lunes a domingo) ---
hoy = df["hora"].dt.date.max()
hoy_dt = datetime.combine(hoy, datetime.min.time())
lunes = hoy_dt - timedelta(days=hoy_dt.weekday())

dias_semana = [lunes + timedelta(days=i) for i in range(7)]
nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

colores = ["#4C9BE8", "#E8774C", "#E8D44C", "#A04CE8", "#E84C8B", "#4CE8D4", "#E8A84C"]

# --- Figura ---
fig = go.Figure()

for i, (dia, nombre) in enumerate(zip(dias_semana, nombres_dias)):
    datos_dia = df[df["hora"].dt.date == dia.date()].copy()

    if datos_dia.empty:
        continue

    datos_dia["hora_normalizada"] = datos_dia["hora"].apply(
        lambda t: lunes.replace(hour=t.hour, minute=t.minute, second=0)
    )

    fig.add_trace(go.Scatter(
        x=datos_dia["hora_normalizada"],
        y=datos_dia["personas"],
        mode="lines+markers",
        name=nombre,
        line=dict(color=colores[i], width=2),
        marker=dict(size=4),
        customdata=datos_dia["porcentaje_num"],
        hovertemplate="%{x|%H:%M} — %{y} personas (%{customdata}%)<extra>" + nombre + "</extra>"
    ))

# --- Formato ---
fig.update_layout(
    title=dict(text="Aforo Dreamfit Aluche", font=dict(size=16)),
    xaxis=dict(
        tickformat="%H:%M",
        dtick=15 * 60 * 1000,
        range=[
            lunes.replace(hour=5, minute=30).isoformat(),
            lunes.replace(hour=23, minute=30).isoformat()
        ],
        tickangle=45,
        title="Hora"
    ),
    yaxis=dict(
        range=[0, 400],
        title="Personas"
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    hovermode="x unified",
    plot_bgcolor="white",
    paper_bgcolor="white",
    shapes=[
        dict(
            type="line",
            x0=lunes.replace(hour=5, minute=30).isoformat(),
            x1=lunes.replace(hour=23, minute=30).isoformat(),
            y0=120, y1=120,
            line=dict(color="green", width=1.5, dash="dash")
        )
    ],
    annotations=[
        dict(
            x=lunes.replace(hour=5, minute=30).isoformat(),
            y=120,
            text="30%",
            showarrow=False,
            yshift=10,
            font=dict(color="green", size=12)
        )
    ]
)

fig.update_xaxes(showgrid=True, gridcolor="#eeeeee")
fig.update_yaxes(showgrid=True, gridcolor="#eeeeee")

fig.write_html("aforo_semana.html")
fig.write_image("aforo_semana.png")
print("Visualización generada: aforo_semana.html y aforo_semana.png")
