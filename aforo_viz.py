import requests
import urllib3
import io
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

carpeta = ""

# --- Cargar datos desde GitHub ---
response = requests.get(
    "https://raw.githubusercontent.com/Mrosg/aforo-gimnasio/main/aforo_dreamfit.csv",
    verify=False
)
df = pd.read_csv(io.StringIO(response.text))
df["hora"] = pd.to_datetime(df["hora"])
df["personas"] = pd.to_numeric(df["personas"])
df["porcentaje_num"] = df["porcentaje"].str.replace("%", "").astype(int)

# --- Obtener todas las semanas disponibles (lunes de cada semana) ---
df["lunes_semana"] = (df["hora"] - pd.to_timedelta(df["hora"].dt.weekday, unit="D")).dt.normalize()
semanas = sorted(df["lunes_semana"].unique())

# Referencia fija para normalizar horas (así el eje X siempre muestra la misma escala horaria)
ref = datetime(2000, 1, 3)  # Lunes fijo como referencia

nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
colores = ["#4C9BE8", "#E8774C", "#E8D44C", "#A04CE8", "#E84C8B", "#4CE8D4", "#E8A84C"]

# --- Orden de días por promedio histórico de personas (mayor a menor para el tooltip) ---
df["dia_semana"] = df["hora"].dt.weekday  # 0=Lunes, 6=Domingo
orden_dias = df.groupby("dia_semana")["personas"].mean().sort_values(ascending=False).index.tolist()

# --- Construir trazas para todas las semanas ---
fig = go.Figure()
trace_meta = []  # lista de (semana_idx, dia_idx) para construir los botones

for s_idx, semana in enumerate(semanas):
    semana_dt = pd.Timestamp(semana).to_pydatetime()
    es_ultima = (s_idx == len(semanas) - 1)

    for i in orden_dias:
        dia = semana_dt + timedelta(days=i)
        datos_dia = df[df["hora"].dt.date == dia.date()].copy()

        if datos_dia.empty:
            continue

        datos_dia["hora_normalizada"] = datos_dia["hora"].apply(
            lambda t: ref.replace(hour=t.hour, minute=t.minute, second=0)
        )

        fig.add_trace(go.Scatter(
            x=datos_dia["hora_normalizada"],
            y=datos_dia["personas"],
            mode="lines+markers",
            name=nombres_dias[i],
            visible=es_ultima,
            showlegend=es_ultima,
            line=dict(color=colores[i], width=2),
            marker=dict(size=4),
            customdata=datos_dia["porcentaje_num"],
            hovertemplate="%{x|%H:%M} — %{y} personas (%{customdata}%)<extra>" + nombres_dias[i] + "</extra>"
        ))
        trace_meta.append((s_idx, i))

# --- Construir botones del dropdown (orden: más reciente primero) ---
buttons = []
for s_idx, semana in reversed(list(enumerate(semanas))):
    semana_label = pd.Timestamp(semana).strftime("%d/%m/%Y")
    visibility = [m[0] == s_idx for m in trace_meta]
    showlegend = [m[0] == s_idx for m in trace_meta]

    buttons.append(dict(
        label=f"Semana {semana_label}",
        method="update",
        args=[
            {"visible": visibility, "showlegend": showlegend},
            {"title": dict(text=f"Aforo Dreamfit Aluche — Semana del {semana_label}")}
        ]
    ))

semana_inicial_label = pd.Timestamp(semanas[-1]).strftime("%d/%m/%Y")

# --- Formato ---
fig.update_layout(
    title=dict(text=f"Aforo Dreamfit Aluche — Semana del {semana_inicial_label}", font=dict(size=16)),
    xaxis=dict(
        tickformat="%H:%M",
        dtick=15 * 60 * 1000,
        range=[
            ref.replace(hour=5, minute=30).isoformat(),
            ref.replace(hour=23, minute=30).isoformat()
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
    updatemenus=[dict(
        active=0,
        buttons=buttons,
        direction="down",
        x=1.0,
        y=1.15,
        xanchor="right",
        yanchor="top",
        showactive=True,
        bgcolor="white",
        bordercolor="#cccccc"
    )],
    shapes=[
        dict(
            type="line",
            x0=ref.replace(hour=5, minute=30).isoformat(),
            x1=ref.replace(hour=23, minute=30).isoformat(),
            y0=120, y1=120,
            line=dict(color="green", width=1.5, dash="dash")
        )
    ],
    annotations=[
        dict(
            x=ref.replace(hour=5, minute=30).isoformat(),
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

fig.write_html(f"{carpeta}aforo_semana.html")
fig.show()
