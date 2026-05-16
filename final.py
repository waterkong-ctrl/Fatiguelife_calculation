import copy
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
            "lat": 33.7,
            "label": "남해",
        },
        "east": {
            "lon": 129.6,
            "lat": 36.8,
            "label": "동해",
        },
    }
    # 실제 해역에 가깝게 잡은 대략적 클릭 폴리곤(위경도)
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

    # 해역 폴리곤 내부 전체를 클릭 가능하게 보이지 않는 포인트를 촘촘히 배치
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
            marker=dict(
                size=20,
                color="rgba(0, 0, 0, 0.0)",
            ),
            customdata=click_keys,
            hovertemplate="클릭해서 해역 선택<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        height=430,
        margin=dict(l=0, r=0, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        mapbox=dict(
            style="carto-positron",
            center=dict(lon=127.8, lat=36.2),
            zoom=5.5,
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


def main():
    st.set_page_config(page_title="해역별 예상 피로수명 계산", page_icon="🌊", layout="wide")

    st.title("해역별 예상 피로수명 계산기")
    st.caption("서해, 남해, 동해 중 선택 후 필요한 파라미터를 입력하면 예상 피로수명을 계산합니다.")

    if "selected_sea" not in st.session_state:
        st.session_state.selected_sea = None

    left_col, right_col = st.columns([1.1, 1.0], gap="large")

    with left_col:
        st.subheader("우리나라 해역 선택")
        st.caption("지도에서 서해/남해/동해 글자를 클릭하면 해당 해역 파라미터 입력창이 열립니다.")
        clicked_key = render_korea_sea_map(st.session_state.selected_sea)
        if clicked_key:
            st.session_state.selected_sea = clicked_key

    selected_key = st.session_state.selected_sea
    submitted = False

    with right_col:
        st.subheader("파라미터 입력")
        if not selected_key:
            st.warning("해역이 아직 선택되지 않았습니다. 왼쪽 지도에서 서해, 남해, 동해 글자 중 하나를 클릭해 주세요.")
            return

        selected_name = DEFAULT_LOCATIONS[selected_key]["name"]
        st.info(f"선택된 해역: {selected_name}")
        base_loc = copy.deepcopy(DEFAULT_LOCATIONS[selected_key])

        with st.form("input_form"):
            st.subheader("공통 파라미터")
            c1, c2, c3 = st.columns(3)
            D = c1.number_input("직경 D (m)", min_value=0.1, value=float(DEFAULT_MONOPILE["D"]), step=0.1)
            thickness = c2.number_input(
                "두께 t (m)", min_value=0.001, value=float(DEFAULT_MONOPILE["thickness"]), step=0.001, format="%.3f"
            )
            L = c3.number_input("파일 길이 L (m)", min_value=1.0, value=float(DEFAULT_MONOPILE["L"]), step=1.0)

            f1, f2, f3 = st.columns(3)
            rho = f1.number_input("해수 밀도 rho (kg/m^3)", min_value=1.0, value=float(DEFAULT_FLUID["rho"]), step=1.0)
            Cd = f2.number_input("항력계수 Cd", min_value=0.01, value=float(DEFAULT_FLUID["Cd"]), step=0.01)
            Cm = f3.number_input("관성계수 Cm", min_value=0.01, value=float(DEFAULT_FLUID["Cm"]), step=0.01)

            st.subheader("고정 적용값")
            st.caption(
                f"S-N: A={DEFAULT_FATIGUE['A']:.2e}, m={DEFAULT_FATIGUE['m']:.1f} | "
                f"{selected_name} 해역: h={base_loc['h']:.1f} m, Uc={base_loc['Uc']:.1f} m/s | "
                "해상상태(SS) 지정값 자동 적용"
            )

            submitted = st.form_submit_button("예상 피로수명 계산")

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


if __name__ == "__main__":
    main()
