import base64
import copy
import html
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

GRAVITY = 9.81
NUM_Z = 200
NUM_T = 400

DEFAULT_MONOPILE = {
    "D": 5.0,
    "thickness": 0.06,
    "L": 30.0,
}

DEFAULT_FLUID = {
    "rho": 1025.0,
    "Cd": 1.0,
    "Cm": 2.0,
}

DEFAULT_FATIGUE = {
    "A": 5.8e11,
    "m": 3.0,
}

DEFAULT_LOCATIONS = {
    "west": {
        "name": "서해",
        "h": 15.0,
        "Uc": 0.3,
        "sea_states": [
            {"name": "SS1", "H": 0.6, "T": 4.5, "days_per_year": 222},
            {"name": "SS2", "H": 1.3, "T": 6.0, "days_per_year": 102},
            {"name": "SS3", "H": 2.3, "T": 7.5, "days_per_year": 38},
            {"name": "SS4", "H": 3.5, "T": 9.0, "days_per_year": 3},
        ],
    },
    "south": {
        "name": "남해",
        "h": 20.0,
        "Uc": 0.5,
        "sea_states": [
            {"name": "SS1", "H": 0.7, "T": 5.0, "days_per_year": 179},
            {"name": "SS2", "H": 1.4, "T": 6.5, "days_per_year": 132},
            {"name": "SS3", "H": 2.6, "T": 8.5, "days_per_year": 52},
            {"name": "SS4", "H": 4.0, "T": 10.0, "days_per_year": 2},
        ],
    },
    "east": {
        "name": "동해",
        "h": 25.0,
        "Uc": 0.5,
        "sea_states": [
            {"name": "SS1", "H": 0.8, "T": 5.0, "days_per_year": 155},
            {"name": "SS2", "H": 1.5, "T": 7.0, "days_per_year": 145},
            {"name": "SS3", "H": 2.8, "T": 9.0, "days_per_year": 61},
            {"name": "SS4", "H": 4.5, "T": 11.0, "days_per_year": 5},
        ],
    },
}

SEA_LAYOUT = ["west", "south", "east"]


def render_korea_sea_map(selected_key):
    sea_points = {
        "west": {
            "lon": 125.1,
            "lat": 36.6,
            "label": "서해",
        },
        "south": {
            "lon": 127.5,
            "lat": 34.0,
            "label": "남해",
        },
        "east": {
            "lon": 129.6,
            "lat": 36.8,
            "label": "동해",
        },
    }
    sea_click_polygons = {
        "west": [
            (123.4, 34.0),
            (126.6, 34.0),
            (126.7, 35.0),
            (126.6, 36.0),
            (126.4, 37.0),
            (126.3, 38.2),
            (125.8, 39.1),
            (123.6, 39.1),
            (123.4, 34.0),
        ],
        "south": [
            (125.4, 32.8),
            (129.9, 32.8),
            (130.1, 33.8),
            (129.7, 34.5),
            (128.9, 34.9),
            (127.5, 35.0),
            (126.3, 34.8),
            (125.6, 34.2),
            (125.4, 32.8),
        ],
        "east": [
            (128.0, 34.4),
            (131.8, 34.4),
            (131.9, 35.6),
            (131.8, 36.8),
            (131.5, 38.0),
            (130.9, 39.3),
            (129.4, 39.5),
            (128.5, 38.8),
            (128.1, 37.6),
            (128.0, 34.4),
        ],
    }

    def point_in_polygon(lon, lat, polygon):
        inside = False
        j = len(polygon) - 1
        for i in range(len(polygon)):
            xi, yi = polygon[i]
            xj, yj = polygon[j]
            intersects = ((yi > lat) != (yj > lat)) and (
                lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-12) + xi
            )
            if intersects:
                inside = not inside
            j = i
        return inside

    fig = go.Figure()
    for sea_key in SEA_LAYOUT:
        p = sea_points[sea_key]
        fig.add_trace(
            go.Scattermapbox(
                lon=[p["lon"]],
                lat=[p["lat"]],
                mode="text",
                text=[p["label"]],
                textposition="middle center",
                textfont=dict(size=24, color="#0B4F9C" if sea_key == selected_key else "#1F1F1F"),
                customdata=[sea_key],
                hovertemplate="%{text} 선택<extra></extra>",
                showlegend=False,
            )
        )

    click_lons = []
    click_lats = []
    click_keys = []
    for sea_key in SEA_LAYOUT:
        polygon = sea_click_polygons[sea_key]
        lons = [p[0] for p in polygon]
        lats = [p[1] for p in polygon]
        lon_vals = np.arange(min(lons), max(lons) + 1e-9, 0.12)
        lat_vals = np.arange(min(lats), max(lats) + 1e-9, 0.12)

        for lon in lon_vals:
            for lat in lat_vals:
                if point_in_polygon(float(lon), float(lat), polygon):
                    click_lons.append(float(lon))
                    click_lats.append(float(lat))
                    click_keys.append(sea_key)

    fig.add_trace(
        go.Scattermapbox(
            lon=click_lons,
            lat=click_lats,
            mode="markers",
            marker=dict(size=20, color="rgba(0, 0, 0, 0.0)"),
            customdata=click_keys,
            hovertemplate="클릭해서 해역 선택<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        mapbox=dict(
            style="carto-positron",
            center=dict(lon=127.8, lat=36.0),
            zoom=5.35,
        ),
    )
    event = st.plotly_chart(
        fig,
        use_container_width=True,
        key="korea_sea_map",
        on_select="rerun",
        selection_mode="points",
        config={"displayModeBar": False},
    )

    selected_from_click = None
    selection = {}
    if isinstance(event, dict):
        selection = event.get("selection", {})
    elif hasattr(event, "selection"):
        selection = event.selection

    if isinstance(selection, dict):
        points = selection.get("points", [])
    else:
        points = getattr(selection, "points", [])
    if points:
        customdata = points[0].get("customdata")
        if customdata in SEA_LAYOUT:
            selected_from_click = customdata

    return selected_from_click


def solve_wave_number(T, h):
    omega = 2 * np.pi / T
    k = omega**2 / GRAVITY
    for _ in range(100):
        f = GRAVITY * k * np.tanh(k * h) - omega**2
        df = GRAVITY * np.tanh(k * h) + GRAVITY * k * h * (1 / np.cosh(k * h)) ** 2
        k -= f / df
    return k


def section_properties(D, t):
    d_inner = D - 2 * t
    I = (np.pi / 64) * (D**4 - d_inner**4)
    c = D / 2
    return I, c


def wave_kinematics(z, time_value, H, T, h, k, Uc):
    a = H / 2
    omega = 2 * np.pi / T
    shape = np.cosh(k * (z + h)) / np.sinh(k * h)
    u = a * omega * shape * np.cos(omega * time_value) + Uc
    du = -a * omega**2 * shape * np.sin(omega * time_value)
    return u, du


def morison(u, du, D, rho, Cd, Cm):
    drag = 0.5 * rho * Cd * D * u * np.abs(u)
    inertia = rho * Cm * (np.pi * D**2 / 4) * du
    return drag + inertia


def sn_cycles(delta_sigma, A, m):
    if delta_sigma <= 0:
        return np.inf
    return A / (delta_sigma**m)


def cycles_per_year(days, T):
    return days * 24 * 3600 / T


def analyze_location(monopile, fluid, fatigue, loc):
    h = loc["h"]
    Uc = loc["Uc"]
    sea_states = loc["sea_states"]

    total_damage = 0.0
    details = []

    for s in sea_states:
        H = s["H"]
        T = s["T"]

        z = np.linspace(-h, 0, NUM_Z)
        t_array = np.linspace(0, T, NUM_T)

        k = solve_wave_number(T, h)

        m_time = []
        for time_value in t_array:
            u, du = wave_kinematics(z, time_value, H, T, h, k, Uc)
            f = morison(u, du, monopile["D"], fluid["rho"], fluid["Cd"], fluid["Cm"])
            M = np.trapezoid(f * (z + h), z)
            m_time.append(M)

        m_time = np.array(m_time)
        I, c = section_properties(monopile["D"], monopile["thickness"])
        sigma = m_time * c / I / 1e6

        delta_sigma = np.max(sigma) - np.min(sigma)
        N = sn_cycles(delta_sigma, fatigue["A"], fatigue["m"])
        n = cycles_per_year(s["days_per_year"], T)

        damage = n / N
        total_damage += damage

        details.append(
            {
                "해상상태": s["name"],
                "응력범위(MPa)": float(delta_sigma),
                "연간손상도": float(damage),
            }
        )

    life = np.inf if total_damage <= 0 else 1 / total_damage
    return life, total_damage, details


def render_fixed_height_image(image_path, height=420):
    if not image_path.exists():
        return

    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div style="height:{height}px; overflow:hidden; border-radius:8px; background:#F8FAFC;">
            <img
                src="data:image/png;base64,{encoded}"
                style="width:100%; height:100%; object-fit:contain; object-position:center;"
                alt="해상풍력 모노파일"
            >
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_monopile_parameter_preview(D, thickness, L):
    display_d = max(float(D), 0.1)
    display_t = max(float(thickness), 0.001)
    display_l = max(float(L), 1.0)

    pile_height = min(max(display_l * 5.0, 120.0), 300.0)
    pile_width = min(max(display_d * 16.0, 36.0), 130.0)
    wall_width = min(max(display_t * 420.0, 4.0), pile_width / 3.0)

    center_x = 130
    seabed_y = 335
    top_y = seabed_y - pile_height
    left_x = center_x - pile_width / 2
    right_x = center_x + pile_width / 2

    fig = go.Figure()
    fig.add_shape(
        type="rect",
        x0=left_x,
        x1=right_x,
        y0=top_y,
        y1=seabed_y,
        line=dict(color="#334155", width=2),
        fillcolor="#CBD5E1",
    )
    fig.add_shape(
        type="rect",
        x0=left_x,
        x1=left_x + wall_width,
        y0=top_y,
        y1=seabed_y,
        line=dict(width=0),
        fillcolor="#64748B",
    )
    fig.add_shape(
        type="rect",
        x0=right_x - wall_width,
        x1=right_x,
        y0=top_y,
        y1=seabed_y,
        line=dict(width=0),
        fillcolor="#64748B",
    )
    fig.add_shape(
        type="line",
        x0=left_x,
        x1=right_x,
        y0=top_y - 22,
        y1=top_y - 22,
        line=dict(color="#0F172A", width=3),
    )
    fig.add_shape(
        type="line",
        x0=right_x + 24,
        x1=right_x + 24,
        y0=top_y,
        y1=seabed_y,
        line=dict(color="#0F172A", width=3),
    )
    fig.add_shape(
        type="line",
        x0=45,
        x1=220,
        y0=seabed_y,
        y1=seabed_y,
        line=dict(color="#A16207", width=8),
    )
    fig.add_annotation(x=center_x, y=top_y - 42, text=f"직경 D = {D:.2f} m", showarrow=False, font=dict(size=13))
    fig.add_annotation(
        x=right_x + 62,
        y=(top_y + seabed_y) / 2,
        text=f"파일 길이 L = {L:.1f} m",
        showarrow=False,
        textangle=90,
        font=dict(size=13),
    )
    fig.add_annotation(
        x=center_x,
        y=seabed_y + 30,
        text=f"두께 t = {thickness:.3f} m",
        showarrow=False,
        font=dict(size=13, color="#475569"),
    )

    fig.update_xaxes(visible=False, range=[0, 260])
    fig.update_yaxes(visible=False, range=[370, 0], scaleanchor="x", scaleratio=1)
    fig.update_layout(
        height=420,
        margin=dict(l=0, r=0, t=15, b=0),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_result_graphs(details, total_damage, life):
    labels = [item["해상상태"] for item in details]
    damages = [item["연간손상도"] for item in details]

    graph_col1, graph_col2 = st.columns(2, gap="large")

    with graph_col1:
        st.subheader("Sea State별 손상 기여도")
        damage_fig = go.Figure(
            data=[
                go.Bar(
                    x=labels,
                    y=damages,
                    marker_color="#2563EB",
                    text=[f"{value:.2e}" for value in damages],
                    textposition="outside",
                    hovertemplate="Sea State: %{x}<br>연간손상도: %{y:.3e}<extra></extra>",
                )
            ]
        )
        damage_fig.update_layout(
            height=390,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="Sea State",
            yaxis_title="연간손상도",
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        st.plotly_chart(damage_fig, use_container_width=True, config={"displayModeBar": False})

    with graph_col2:
        st.subheader("누적 손상도(D) vs 시간")
        if total_damage > 0 and np.isfinite(life):
            time_years = np.linspace(0, max(life * 1.15, 1.0), 120)
            cumulative_damage = total_damage * time_years
            x_range = [0, max(life * 1.15, 1.0)]
        else:
            time_years = np.linspace(0, 30, 120)
            cumulative_damage = np.zeros_like(time_years)
            x_range = [0, 30]

        cumulative_fig = go.Figure()
        cumulative_fig.add_trace(
            go.Scatter(
                x=time_years,
                y=cumulative_damage,
                mode="lines",
                line=dict(color="#DC2626", width=3),
                name="누적 손상도",
                hovertemplate="시간: %{x:.2f} years<br>D: %{y:.3f}<extra></extra>",
            )
        )
        cumulative_fig.add_hline(
            y=1,
            line_dash="dash",
            line_color="#111827",
            annotation_text="D=1 피로파괴",
            annotation_position="top left",
        )
        if total_damage > 0 and np.isfinite(life):
            cumulative_fig.add_vline(
                x=life,
                line_dash="dot",
                line_color="#DC2626",
                annotation_text=f"{life:.2f} years",
                annotation_position="top right",
            )
        cumulative_fig.update_layout(
            height=390,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="시간 (years)",
            yaxis_title="누적 손상도 D",
            xaxis=dict(range=x_range),
            yaxis=dict(range=[0, max(float(np.max(cumulative_damage)) * 1.05, 1.15)]),
            paper_bgcolor="white",
            plot_bgcolor="white",
            showlegend=False,
        )
        st.plotly_chart(cumulative_fig, use_container_width=True, config={"displayModeBar": False})


def render_compact_table(rows):
    if not rows:
        return

    headers = list(rows[0].keys())
    header_html = "".join(f"<th>{html.escape(str(header))}</th>" for header in headers)
    body_html = ""
    for row in rows:
        body_html += "<tr>"
        body_html += "".join(f"<td>{html.escape(str(row[header]))}</td>" for header in headers)
        body_html += "</tr>"

    st.markdown(
        f"""
        <div style="display:inline-block; margin:6px 0 10px 0;">
            <table style="border-collapse:collapse; table-layout:auto; width:auto; font-size:15px;">
                <thead>
                    <tr>{header_html}</tr>
                </thead>
                <tbody>
                    {body_html}
                </tbody>
            </table>
        </div>
        <style>
            table th {{
                background:#F1F5F9;
                border:1px solid #CBD5E1;
                padding:8px 14px;
                text-align:center;
                white-space:nowrap;
            }}
            table td {{
                border:1px solid #CBD5E1;
                padding:8px 14px;
                text-align:center;
                white-space:nowrap;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_calculation_process(monopile, fluid, fatigue, loc, details, total_damage, life):
    st.subheader("주요 계산과정")

    wave_rows = []
    fatigue_rows = []
    damage_rows = []
    for sea_state, result in zip(loc["sea_states"], details):
        omega = 2 * np.pi / sea_state["T"]
        k = solve_wave_number(sea_state["T"], loc["h"])
        delta_sigma = result["응력범위(MPa)"]
        n = cycles_per_year(sea_state["days_per_year"], sea_state["T"])
        N = np.inf if result["연간손상도"] <= 0 else n / result["연간손상도"]
        wave_rows.append(
            {
                "Sea State": sea_state["name"],
                "H (m)": f"{sea_state['H']:.2f}",
                "T (s)": f"{sea_state['T']:.2f}",
                "omega (rad/s)": f"{omega:.3f}",
                "k (1/m)": f"{k:.4f}",
            }
        )
        fatigue_rows.append(
            {
                "Sea State": sea_state["name"],
                "Delta sigma (MPa)": f"{delta_sigma:.3f}",
                "N = A/(Delta sigma^m)": "inf" if np.isinf(N) else f"{N:.3e}",
            }
        )
        damage_rows.append(
            {
                "Sea State": sea_state["name"],
                "days/year": f"{sea_state['days_per_year']:.0f}",
                "n = days*24*3600/T": f"{n:.3e}",
                "D_i = n/N": f"{result['연간손상도']:.3e}",
            }
        )

    with st.expander("1. 파랑하중 계산", expanded=False):
        wave_table = "| Sea State | H (m) | T (s) | omega (rad/s) | k (1/m) |\n"
        wave_table += "|---|---:|---:|---:|---:|\n"
        for row in wave_rows:
            wave_table += (
                f"| {row['Sea State']} | {row['H (m)']} | {row['T (s)']} | "
                f"{row['omega (rad/s)']} | {row['k (1/m)']} |\n"
            )
        st.markdown(
            f"""
            선택 해역 입력값을 파랑하중 식에 넣어 계산합니다.

            {wave_table}

            - 분산식 대입: `omega^2 = 9.81 * k * tanh(k * {loc['h']:.1f})`
            - 속도식 대입: `u(z,t) = (H/2) * omega * cosh(k(z+{loc['h']:.1f})) / sinh(k*{loc['h']:.1f}) * cos(omega*t) + {loc['Uc']:.2f}`
            - Morison 식 대입:
              `F = 0.5 * {fluid['rho']:.1f} * {fluid['Cd']:.2f} * {monopile['D']:.2f} * u|u| + {fluid['rho']:.1f} * {fluid['Cm']:.2f} * (pi * {monopile['D']:.2f}^2 / 4) * du/dt`
            """
        )

    with st.expander("2. 구조응답 및 응력 계산", expanded=False):
        I, c = section_properties(monopile["D"], monopile["thickness"])
        d_inner = monopile["D"] - 2 * monopile["thickness"]
        st.markdown(
            f"""
            - 내경 계산: `d_i = D - 2t = {monopile['D']:.2f} - 2 * {monopile['thickness']:.3f} = {d_inner:.3f} m`
            - 단면 2차모멘트:
              `I = pi/64 * ({monopile['D']:.2f}^4 - {d_inner:.3f}^4) = {I:.3e} m^4`
            - 외측거리:
              `c = D/2 = {monopile['D']:.2f}/2 = {c:.3f} m`
            - 각 시간의 굽힘응력:
              `sigma(t) = M(t) * {c:.3f} / {I:.3e} / 1e6`
            - 응력범위:
              `Delta sigma = max(sigma) - min(sigma)`로 Sea State별 값을 구합니다.
            """
        )

    with st.expander("3. 피로수명평가", expanded=False):
        fatigue_table = "| Sea State | Delta sigma (MPa) | N = A/(Delta sigma^m) |\n"
        fatigue_table += "|---|---:|---:|\n"
        for row in fatigue_rows:
            fatigue_table += f"| {row['Sea State']} | {row['Delta sigma (MPa)']} | {row['N = A/(Delta sigma^m)']} |\n"
        st.markdown(
            f"""
            S-N 곡선 상수 `A = {fatigue['A']:.2e}`, `m = {fatigue['m']:.1f}`를 사용합니다.

            - 대입식: `N = {fatigue['A']:.2e} / (Delta sigma ^ {fatigue['m']:.1f})`

            {fatigue_table}
            """
        )

    with st.expander("4. 누적손상평가", expanded=False):
        life_text = "무한대" if np.isinf(life) else f"{life:.2f} years"
        damage_table = "| Sea State | days/year | n = days*24*3600/T | D_i = n/N |\n"
        damage_table += "|---|---:|---:|---:|\n"
        for row in damage_rows:
            damage_table += (
                f"| {row['Sea State']} | {row['days/year']} | {row['n = days*24*3600/T']} | {row['D_i = n/N']} |\n"
            )
        st.markdown(
            f"""
            각 Sea State의 연간 반복횟수와 손상도를 실제 값으로 계산합니다.

            {damage_table}

            - 총 연간 손상도:
              `D_year = ΣD_i = {total_damage:.3e}`
            - 예상 피로수명:
              `Life = 1 / D_year = 1 / {total_damage:.3e} = {life_text}`
            - 그래프에서 `D = 1`이 되는 시점이 피로파괴 기준입니다.
            """
        )


def render_calculation_process_readable(monopile, fluid, fatigue, loc, details, total_damage, life):
    st.subheader("주요 계산과정")

    wave_rows = []
    fatigue_rows = []
    damage_rows = []

    for sea_state, result in zip(loc["sea_states"], details):
        omega = 2 * np.pi / sea_state["T"]
        k = solve_wave_number(sea_state["T"], loc["h"])
        delta_sigma = result["응력범위(MPa)"]
        n = cycles_per_year(sea_state["days_per_year"], sea_state["T"])
        damage = result["연간손상도"]
        N = np.inf if damage <= 0 else n / damage

        wave_rows.append(
            {
                "Sea State": sea_state["name"],
                "H (m)": round(sea_state["H"], 3),
                "T (s)": round(sea_state["T"], 3),
                "omega = 2pi/T (rad/s)": round(omega, 4),
                "k (1/m)": round(k, 5),
            }
        )
        fatigue_rows.append(
            {
                "Sea State": sea_state["name"],
                "Delta sigma (MPa)": f"{delta_sigma:.3f}",
                "대입식": f"N = {fatigue['A']:.2e} / ({delta_sigma:.3f}^{fatigue['m']:.1f})",
                "N": "inf" if np.isinf(N) else f"{N:.3e}",
            }
        )
        damage_rows.append(
            {
                "Sea State": sea_state["name"],
                "대입식": f"n = {sea_state['days_per_year']:.0f} * 24 * 3600 / {sea_state['T']:.2f}",
                "n": f"{n:.3e}",
                "D_i = n/N": f"{damage:.3e}",
            }
        )

    with st.expander("1. 파랑하중 계산", expanded=False):
        st.markdown("**기본식**")
        st.markdown(
            """
            - `omega = 2pi / T`
            - `omega^2 = g k tanh(kh)`
            - `u(z,t) = (H/2) omega cosh(k(z+h)) / sinh(kh) cos(omega t) + Uc`
            - `F = 0.5 rho Cd D u|u| + rho Cm (pi D^2 / 4) du/dt`
            """
        )
        st.markdown("**값 대입**")
        st.markdown(
            f"""
            - 분산식: `omega^2 = 9.81 * k * tanh(k * {loc['h']:.1f})`
            - 속도식: `u(z,t) = (H/2) * omega * cosh(k(z+{loc['h']:.1f})) / sinh(k*{loc['h']:.1f}) * cos(omega*t) + {loc['Uc']:.2f}`
            - Morison 식: `F = 0.5 * {fluid['rho']:.1f} * {fluid['Cd']:.2f} * {monopile['D']:.2f} * u|u| + {fluid['rho']:.1f} * {fluid['Cm']:.2f} * (pi * {monopile['D']:.2f}^2 / 4) * du/dt`
            """
        )
        render_compact_table(wave_rows)

    with st.expander("2. 구조응답 및 응력 계산", expanded=False):
        I, c = section_properties(monopile["D"], monopile["thickness"])
        d_inner = monopile["D"] - 2 * monopile["thickness"]
        st.markdown("**기본식**")
        st.markdown(
            """
            - `d_i = D - 2t`
            - `I = pi/64 * (D^4 - d_i^4)`
            - `c = D/2`
            - `sigma = M c / I`
            - `Delta sigma = max(sigma) - min(sigma)`
            """
        )
        st.markdown("**값 대입 및 결과**")
        st.markdown(
            f"""
            - `d_i = {monopile['D']:.2f} - 2 * {monopile['thickness']:.3f} = {d_inner:.3f} m`
            - `I = pi/64 * ({monopile['D']:.2f}^4 - {d_inner:.3f}^4) = {I:.3e} m^4`
            - `c = {monopile['D']:.2f} / 2 = {c:.3f} m`
            - `sigma(t) = M(t) * {c:.3f} / {I:.3e} / 1e6`
            """
        )

    with st.expander("3. 피로수명평가", expanded=False):
        st.markdown("**기본식**")
        st.markdown("- `N = A / (Delta sigma^m)`")
        st.markdown("**값 대입 및 결과**")
        st.markdown(f"- `A = {fatigue['A']:.2e}`, `m = {fatigue['m']:.1f}`")
        render_compact_table(fatigue_rows)

    with st.expander("4. 누적손상평가", expanded=False):
        life_text = "무한대" if np.isinf(life) else f"{life:.2f} years"
        st.markdown("**기본식**")
        st.markdown(
            """
            - `n = days_per_year * 24 * 3600 / T`
            - `D_i = n / N`
            - `D_year = sum(D_i)`
            - `Life = 1 / D_year`
            """
        )
        st.markdown("**값 대입 및 결과**")
        render_compact_table(damage_rows)
        st.markdown(
            f"""
            - `D_year = sum(D_i) = {total_damage:.3e}`
            - `Life = 1 / D_year = 1 / {total_damage:.3e} = {life_text}`
            """
        )


def main():
    st.set_page_config(page_title="해역별 모노파일 예상 피로수명 계산", page_icon="🌊", layout="wide")

    st.title("해역별 모노파일 예상 피로수명 계산")
    st.divider()

    if "selected_sea" not in st.session_state:
        st.session_state.selected_sea = None

    intro_col, map_col = st.columns([1.0, 1.1], gap="large")

    with intro_col:
        st.subheader("계산 대상: 해상풍력 모노파일")
        monopile_image = Path(__file__).resolve().parent / "assets" / "monopile_intro.png"
        render_fixed_height_image(monopile_image)
        st.markdown(
            """
            <div style="margin-top:10px; font-size:15px; line-height:1.65; color:#374151;">
                모노파일은 해상풍력 하부구조물 중 하나로, 해저 지반에 삽입되는 대형 원통형 강관입니다.
                파랑과 해류에 의해 반복 하중을 받기 때문에 해역별 환경 조건을 반영한 피로수명 검토가 필요합니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with map_col:
        st.subheader("우리나라 해역 선택")
        st.caption("지도에서 동해, 서해, 남해 중 한 지점을 선택하면 모노파일 피로수명 계산을 위한 파라미터 입력창이 열립니다.")
        clicked_key = render_korea_sea_map(st.session_state.selected_sea)
        if clicked_key:
            st.session_state.selected_sea = clicked_key

    selected_key = st.session_state.selected_sea
    submitted = False

    if not selected_key:
        st.write("")
        st.info("지도에서 동해, 서해, 남해 중 하나를 선택하면 파라미터 입력창이 나타납니다.")
        return

    selected_name = DEFAULT_LOCATIONS[selected_key]["name"]
    base_loc = copy.deepcopy(DEFAULT_LOCATIONS[selected_key])

    st.divider()
    st.subheader("파라미터 입력")
    input_col, guide_col = st.columns([1.4, 0.8], gap="large")

    with input_col:
        st.info(f"선택된 해역: {selected_name}")

        st.subheader("공통 파라미터")
        c1, c2, c3 = st.columns(3)
        D = c1.number_input("직경 D (m)", min_value=0.1, value=float(DEFAULT_MONOPILE["D"]), step=0.1)
        thickness = c2.number_input(
            "두께 t (m)",
            min_value=0.001,
            value=float(DEFAULT_MONOPILE["thickness"]),
            step=0.001,
            format="%.3f",
        )
        L = c3.number_input("파일 길이 L (m)", min_value=1.0, value=float(DEFAULT_MONOPILE["L"]), step=1.0)

        f1, f2, f3 = st.columns(3)
        rho = f1.number_input("해수 밀도 rho (kg/m^3)", min_value=1.0, value=float(DEFAULT_FLUID["rho"]), step=1.0)
        Cd = f2.number_input("항력계수 Cd", min_value=0.01, value=float(DEFAULT_FLUID["Cd"]), step=0.01)
        Cm = f3.number_input("관성계수 Cm", min_value=0.01, value=float(DEFAULT_FLUID["Cm"]), step=0.01)

        st.subheader(f"{selected_name} 해상상태 파라미터")
        st.markdown(
            f"""
            <div style="font-size:18px; line-height:1.7; color:#1F2937;">
                <b>S-N:</b> A={DEFAULT_FATIGUE['A']:.2e}, m={DEFAULT_FATIGUE['m']:.1f}<br>
                <b>{selected_name} 해역:</b> h={base_loc['h']:.1f} m, Uc={base_loc['Uc']:.1f} m/s<br>
                해상상태(SS) 지정값 자동 적용
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")
        submitted = st.button("예상 피로수명 계산", type="primary")

    with guide_col:
        st.subheader("모노파일 파라미터 미리보기")
        render_monopile_parameter_preview(D, thickness, L)

    if submitted:
        validation_errors = []
        if D <= 0:
            validation_errors.append("직경 D는 0보다 커야 합니다.")
        if thickness <= 0:
            validation_errors.append("두께 t는 0보다 커야 합니다.")
        if thickness * 2 >= D:
            validation_errors.append("두께 t는 직경 D의 절반보다 작아야 합니다. (D > 2t)")
        if L <= 0:
            validation_errors.append("파일 길이 L은 0보다 커야 합니다.")
        if rho <= 0:
            validation_errors.append("해수 밀도 rho는 0보다 커야 합니다.")
        if Cd <= 0:
            validation_errors.append("항력계수 Cd는 0보다 커야 합니다.")
        if Cm <= 0:
            validation_errors.append("관성계수 Cm는 0보다 커야 합니다.")

        if validation_errors:
            for err in validation_errors:
                st.error(err)
            return

        monopile = {"D": D, "thickness": thickness, "L": L}
        fluid = {"rho": rho, "Cd": Cd, "Cm": Cm}
        fatigue = {"A": DEFAULT_FATIGUE["A"], "m": DEFAULT_FATIGUE["m"]}

        loc = {
            "name": selected_name,
            "h": base_loc["h"],
            "Uc": base_loc["Uc"],
            "sea_states": base_loc["sea_states"],
        }

        with st.spinner("예상 피로수명 계산 중입니다..."):
            life, total_damage, details = analyze_location(monopile, fluid, fatigue, loc)

        st.success(f"{selected_name} 예상 피로수명 계산 완료")
        k1, k2 = st.columns(2)
        if np.isinf(life):
            k1.metric("예상 피로수명", "무한대")
        else:
            k1.metric("예상 피로수명", f"{life:.2f} years")
        k2.metric("총 연간 손상도", f"{total_damage:.3e}")

        st.dataframe(details, use_container_width=True)
        render_result_graphs(details, total_damage, life)
        render_calculation_process_readable(monopile, fluid, fatigue, loc, details, total_damage, life)


if __name__ == "__main__":
    main()
